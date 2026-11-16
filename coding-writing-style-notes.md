# Learning clarity from soradacroi's projects

Reviewed on 10 November 2026. This is a sample-based style review, not an audit of every repository or a claim about authorship. I read source and documentation in four projects; I did not run their programs or reproduce their results. The links below pin the reviewed versions.

The useful habit is making decisions and observations visible. Casual spelling, jokes, and an unfinished appearance do not establish whether someone used AI. Borrow the reasoning habits and develop your own voice.

## What to notice

### 1. Start with the reason the project exists

The [classifier README](https://github.com/soradacroi/nb-text-classifier/blob/5adf483caa75d65aa39289690053a041f5f5e995/README.md) starts with an emotion-detection project that led the author to Naive Bayes. That gives the implementation a concrete purpose.

Apply it: write two sentences explaining what you wanted to do and what you chose to try. Use your actual motivation; don't invent a discovery story.

### 2. Explain an operation through a small transformation

That README follows one sentence through negation handling and then n-gram generation. The reader sees the intermediate representation, rather than just being told the model handles context. It also connects larger n-grams to vocabulary size and possible overfitting, though its preferred settings are anecdotal.

Apply it: show input → intermediate value → output. For a data-analysis assignment, show a few rows before and after a transformation and explain why it is needed.

### 3. Keep the algorithm visible

The [classifier implementation](https://github.com/soradacroi/nb-text-classifier/blob/5adf483caa75d65aa39289690053a041f5f5e995/nb_text_classifier.py) exposes feature extraction, counting, priors, and prediction in separate methods. Dictionaries and loops make the underlying mechanism inspectable. Names such as `docs_per_class` and `feat_count_in_class` help connect quantities to their purpose.

Apply it: use names from the problem and functions with a clear responsibility. Add an abstraction when it solves a concrete problem. A small script does not need a framework; a coherent model object can reasonably use a class.

### 4. Compare against something simpler

The [character generator experiments](https://github.com/soradacroi/markov-text-generator/blob/69db3708df87dea249cfed9c959a3d3141567cb4/gen_words.py) compare learned transitions with random letters, vary stopping probability, and then increase model order. The saved outputs let readers inspect the author's qualitative judgments.

Apply it: record a baseline, change one relevant choice, and compare the same kind of output. For numerical claims, use a defined metric and controlled evaluation. A few appealing samples are illustrative evidence, not a reliable performance estimate.

### 5. Connect a limitation to the code that causes it

In that generator, training skips words shorter than `order`, and generation begins with an `order`-length prefix. The author notices that increasing the order prevents shorter words from appearing. This is a specific implementation limitation, not a universal property of every character Markov model.

Apply it: write “This version cannot do X because Y.” Explain the mechanism behind the limitation.

### 6. Record revisions and uncertainty honestly

The [genomics README](https://github.com/soradacroi/Genomic-ML-From-Scratch/blob/e037931d6f55811d97f7b69ea4600966d4e46b84/README.md) records changes to shuffling, datasets, and the author's interpretation of the method. It reads like a working notebook because the conclusions remain provisional. Its speculation about biological causes is not established by the reported experiments.

Apply it: distinguish “I observed,” “I suspect,” and “I will test.” Preserve useful failed attempts in an experiment log. Record the split, seed, metric, and sample counts when they affect the conclusion.

### 7. Let personality come from real details

The generator's comments include reactions to specific outputs and unrelated personal asides. Those details give it a recognizable voice, but many interrupt the technical explanation.

Apply it: retain concrete observations and your natural phrasing. Move diary material into notes when it distracts from maintained code. There is no need to manufacture typos, slang, hesitation, or frustration.

## What I would improve rather than copy

- **Naming is uneven.** The [word-level generator](https://github.com/soradacroi/markov-text-generator/blob/69db3708df87dea249cfed9c959a3d3141567cb4/v1.py) uses abbreviated names such as `p_w`. Prefer `previous_word` when the abbreviation makes the reader decode it.
- **Short code can conceal a boundary error.** That generator starts its loop at zero and accesses `data[i-1]`, creating a last-word-to-first-word transition. Make that wraparound an explicit choice or iterate over adjacent pairs.
- **Plain loops still need edge-case reasoning.** In [counting.py](https://github.com/soradacroi/Genomic-ML-From-Scratch/blob/e037931d6f55811d97f7b69ea4600966d4e46b84/src/counting/counting.py), `split_g` stops before the last valid window and cannot terminate for a sequence shorter than `n`. These are deductions from reading the loop, not executed test results.
- **Readable prose can disagree with implementation.** The classifier README describes smoothing in terms of previously unseen words; prediction actually skips features absent from the vocabulary. Smoothing there addresses in-vocabulary features with zero counts in a class. Check explanations against the actual branch conditions.
- **A demo should work as written.** The classifier README's setup uses an import name different from the current source filename and trailing commas that turn the stopword and negation sets into tuples. These are useful reminders to check examples instead of judging quality by tone.
- **Avoid broad exception handling and repeated blocks.** [todai.py](https://github.com/soradacroi/todai/blob/0083eb71a9a41d17cbe1c35e139189b662666716/todai.py) uses a bare `except` and repeats widget construction. Catch the expected failure and share the common setup.

These are learning projects. Their roughness does not cancel out their useful ideas, and their personal tone does not make every design choice worth adopting.

## Checklist for my own work

- [ ] I can explain the purpose in two ordinary sentences.
- [ ] I can trace one input through every important intermediate value to the output.
- [ ] Names explain what values mean; units and shapes are clear where relevant.
- [ ] Each function has a clear job, and the main flow is easy to follow.
- [ ] Every abstraction solves a problem present in this project.
- [ ] Comments explain intent, assumptions, or surprising behavior.
- [ ] The explanation includes one concrete example.
- [ ] Results state what was measured and under what conditions.
- [ ] Observations, guesses, and future work are distinguishable.
- [ ] I checked a normal case and a meaningful boundary case.
- [ ] I removed filler, stale comments, and claims the code does not support.
- [ ] I can explain and modify any AI-assisted code I keep.

## A reusable instruction for AI assistance

> Use direct, readable code appropriate to this project's scale and conventions. Choose names from the problem, keep data flow visible, and explain non-obvious decisions. In prose, state the purpose, show a concrete example, and distinguish measured results from guesses. Avoid inflated descriptions, unnecessary abstraction, and comments that repeat the code. Do not invent experiments, personal anecdotes, or mistakes to make the work appear human. Explain any part I need to understand before accepting the result.

## Ten-minute practice

Choose a small function you already use. Close the source and describe its input, output, and steps. Reimplement it from those notes. Check one typical input and one boundary case. Then write four sentences: what it does, why you chose this approach, what you checked, and what remains limited.

Compare your version with the original for clarity and correctness. The ability to reconstruct and explain the mechanism is the progress to look for.
