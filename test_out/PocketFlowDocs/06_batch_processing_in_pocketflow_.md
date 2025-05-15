# Chapter 6: Batch Processing in PocketFlow

Welcome back! In the previous chapter, we explored [Flows (`Flow`, `AsyncFlow`)](05_flows___flow____asyncflow___.md) — the orchestrators that manage how Nodes run step-by-step in your workflow. Now, imagine you have *many* similar tasks to do, like translating a document into several languages or processing a bunch of images. Doing these one at a time could take a long time or make your code complex.

**This is where Batch Processing in PocketFlow shines!**

---

## Why Batch Processing?

Think about a librarian who needs to process **hundreds of books**:

- One way: She reads and processes each book **one by one** (slow but simple).
- Another way: She calls in a **team** so several books can be processed **at the same time** (faster but requires coordination).

Batch Processing helps you by grouping similar tasks and running them sequentially or in parallel more easily and efficiently.

In PocketFlow, you have special classes to help:

| Tool                      | What It Does                                       | Real World Analogy                    |
|---------------------------|---------------------------------------------------|--------------------------------------|
| `BatchNode`               | Runs the task one item after another (sequential) | The librarian processing books one by one |
| `AsyncParallelBatchNode`  | Runs tasks concurrently with async calls           | A team of librarians working in parallel |
| `BatchFlow`               | Runs a small workflow multiple times sequentially | A director shooting the same scene repeatedly with different actors |
| `AsyncParallelBatchFlow`  | Runs multiple sub-workflows concurrently            | Multiple film crews shooting scenes at the same time |

---

## Our Example Use Case: Translate a Document into Multiple Languages

Imagine you want to translate the sentence:

> "Hello, welcome to PocketFlow!"

...into **Spanish, French, and German**.

Doing this one language at a time is slow. Using PocketFlow’s batch processing, you can run these translations in sequence or concurrently, so your code stays simple and fast!

---

## 1. `BatchNode`: Running Tasks Sequentially on Batches

`BatchNode` helps you process a **list of items one by one**. It breaks down the job into:

- **`prep()`**: Prepare the list of items to work on.
- **`exec(item)`**: Process one item.
- **`post()`**: Combine results or finalize.

### Simple Example: Processing Words One-by-One

```python
from pocketflow import BatchNode

class WordProcessor(BatchNode):
    def prep(self, shared):
        return ["apple", "banana", "cherry"]  # List of words

    def exec(self, word):
        return word.upper()  # Capitalize each word

    def post(self, shared, prep_res, exec_res_list):
        shared["processed_words"] = exec_res_list
        return "done"
```

**What happens?**

- `prep` returns a list of words.
- `exec` runs for each word, making them uppercase.
- `post` collects all results and stores them in `shared`.

If you ran this, `shared["processed_words"]` would be:

```python
['APPLE', 'BANANA', 'CHERRY']
```

---

## 2. `AsyncParallelBatchNode`: Running Async Tasks Concurrently

What if processing each item is an async task — like calling a web API? `AsyncParallelBatchNode` lets you run all these async tasks **at the same time**, speeding things up.

### Continuing Our Translation Example

```python
from pocketflow import AsyncParallelBatchNode

class TranslateNode(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        text = shared.get("text", "")
        languages = shared.get("languages", [])
        return [(text, lang) for lang in languages]  # Prepare pairs

    async def exec_async(self, data):
        text, language = data
        # Pretend to call an async API to translate (simplified)
        print(f"Translating to {language}")
        return f"Translated '{text}' to {language}"

    async def post_async(self, shared, prep_res, exec_res_list):
        shared["translations"] = exec_res_list
        print(f"All translations done!")
        return "done"
```

**How this works:**

- `prep_async` gives a list of items `(text, language)` to process.
- `exec_async` translates one item asynchronously.
- PocketFlow runs multiple `exec_async` calls in parallel.
- `post_async` collects all translation results.

If `shared` started with:

```python
{
    "text": "Hello, welcome to PocketFlow!",
    "languages": ["Spanish", "French", "German"]
}
```

After running, `shared["translations"]` might contain:

```python
[
    "Translated 'Hello, welcome to PocketFlow!' to Spanish",
    "Translated 'Hello, welcome to PocketFlow!' to French",
    "Translated 'Hello, welcome to PocketFlow!' to German"
]
```

---

## 3. `BatchFlow`: Running a Sub-Workflow Multiple Times Sequentially

Sometimes the work is more complex than just one step, and you want to run a **whole workflow (set of connected Nodes)** many times with different inputs.

`BatchFlow` does exactly this, running the *sub-workflow* multiple times *in sequence*.

### Simple Concept:

Imagine you have a workflow that:

- Loads an image,
- Applies a filter,
- Saves the result.

You want to do this for many images or filters.

`BatchFlow` will:

- Prepare a list of parameter sets (e.g., image + filter),
- Run the entire workflow for each set — one after the other.

### Example Outline:

```python
from pocketflow import BatchFlow

class ImageBatchFlow(BatchFlow):
    def prep(self, shared):
        images = ["cat.jpg", "dog.jpg"]
        filters = ["grayscale", "blur"]
        params = []
        for img in images:
            for f in filters:
                params.append({"image": img, "filter": f})
        return params
```

- Each `params` dictionary is passed as inputs to the sub-workflow run.
- All runs happen one by one, sequentially.

---

## 4. `AsyncParallelBatchFlow`: Running Sub-Workflows in Parallel

`AsyncParallelBatchFlow` is the async, parallel version of `BatchFlow`.

If your sub-workflow is async or involves waiting operations, this class lets you run **many sub-workflows at the same time**.

---

## What REALLY Happens When You Run a Batch?

Let’s see the big picture with a simple diagram for `AsyncParallelBatchNode`. Imagine translating a sentence to 3 languages:

```mermaid
sequenceDiagram
    participant UserApp
    participant TranslateNode as AsyncParallelBatchNode
    participant EventLoop

    UserApp->>TranslateNode: run_async(shared)
    TranslateNode->>TranslateNode: prep_async(shared) -> [(text, "ES"), (text, "FR"), (text, "DE")]
    TranslateNode->>EventLoop: asyncio.gather(
        exec_async((text, "ES")),
        exec_async((text, "FR")),
        exec_async((text, "DE"))
    )
    EventLoop-->>TranslateNode: Returns list of translation results
    TranslateNode->>UserApp: post_async(...) returns final action
```

- The `prep_async` prepares the batch.
- `exec_async` runs multiple times concurrently via the event loop.
- Results collected in a list returned to `post_async`.
- Final action returned to the Flow/FlowRunner.

---

## Diving Deeper: Simple Code Behind `BatchNode`

```python
class BatchNode(Node):
    def _exec(self, items):
        results = []
        for item in items:
            result = super()._exec(item)  # exec() for single item
            results.append(result)
        return results
```

- `_exec` loops through the items.
- Calls `exec()` on each item one at a time.
- Returns list of results to `post`.

---

## And Behind `AsyncParallelBatchNode`

```python
class AsyncParallelBatchNode(AsyncNode, BatchNode):
    async def _exec(self, items):
        tasks = [super()._exec(item) for item in items]  # Creates coroutines
        results = await asyncio.gather(*tasks)           # Runs concurrently
        return results
```

- Creates an async task for each item.
- Uses `asyncio.gather` to run them all in parallel.
- Awaits completion and collects results.

---

## Summary: What Have We Learned?

- **Batch processing** helps run similar tasks over collections: either **sequentially** or **in parallel**.
- `BatchNode` is the easy way to do sequential batch processing.
- `AsyncParallelBatchNode` lets you run many async tasks simultaneously, making things faster!
- When your "task" is actually a small workflow, use `BatchFlow` (sequential) or `AsyncParallelBatchFlow` (parallel).
- Batch abstractions keep your code clean, modular, and efficient.

---

## What’s Next?

Now that you understand how PocketFlow lets you handle many items or workflows efficiently using batch processing, the next step is to dive deeper into **asynchronous processing**, understanding how to build responsive and scalable Nodes and Flows that deal with waiting on external tasks.

Check out the next chapter: [Chapter 7: Asynchronous Processing and AsyncNode/AsyncFlow](07_asynchronous_processing_and_asyncnode_asyncflow_.md)

---

Happy batching and building powerful AI workflows with PocketFlow!

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)