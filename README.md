# pyTrace

Pytrace provides fixation algorithms for aggregating gazes, as well as tools to help you deal with edits that occur during eyetracking sessions.


## Getting started

pyTrace comes with a command line interface as well as a python library. 

To use either version, you need 3 things:
* gaze file output
* changelog
* original source file(s)



To get started:

```python
# import pytrace
from pytrace import fixation_filter, Tracker

# run fixation filter to get fixations
fixations = fixation_filter(gazes, changelog, sources, **opts)

# Now track edits using Tracker

tracker = Tracker(fixations, changelog, sources)

```

Internally, tracker assigns a unique id to each token in the source code that is unique across time. You can use the `id` to track how a token moves around, 
along with any fixations on the token.


### Tracking tokens across edits
Lets say you have an original source file, along with some fixations & changes.
```python
source_original = """
    int x = 22;
    int y = 33;
"""
fixations = [{ "line": 1, "col": 4, time: 0} # points to the 'i' in 'int' from the line 'int x = 22;'
,...
]
changelog = [{"line": 1, "col": 0, "type": "insert", text: "\n", time=1}] # adding a new line 
```

You create a tracker `Tracker`:

```python
tracker = Tracker(fixations, change_log, source_original)

# option 1
# get all tokens at time 0
orignal_tokens = tracker.get_tokens_at_time(0) # [Token('int'), Token('x'), Token('='), ...]

# lets get the token for 'int'
token = original_tokens[0]

# option 2
# or you could simply do this:
token = tracker.get_token_with_text("int") # Token('int')
```

Each token has an `id`, `syntactic_category`, `start` and `end` indices, `last_edited` (the last time this token changed either position or text), and some other properties.

Now lets say you wanna see how this token changed over time

```python
history = tracker.token_history(token)#

# want:
[{ token: token,
   changed: true | false, 
   gazes: [...],
   snapshot: int
  },
  ],
  
```

This `tracker.token_history(token)` will give you all the different versions of this token. Each `token` contains a `last_edited` node, which tells you the timestamp at which the last edit was made.



### Getting all gazes over a particular identifier

```python
    gazes = tracker.get_gazes(token=token)
    # gazes is all gazes that 
    # are mapped to this given token
```

### Getting gazes within a time window
```python
gazes = tracker.gazes(time_window=[0, 1])
# all gazes from time 0 to time 1
```


### Getting gazes in a certain span of the text

```python
gazes = tracker.gazes(
    span=(
        (0, 3), # all gazes from line 0, col 3
        (4, 5)  # to line 4, col 5
    )
)
```

### Combinations
```python
    gazes = tracker.gazes(
        span=(..),
        token=..,
        time_window=..
    )
    # > all gazes on the given token within the given line/col span
    # within the given time_window
```

### Getting a specific token to use with queries

```
    tracker.get_token(text="int", line=3)
    # > first 'int' on line 3

    tracker.get_token(line=3, col=5)
    # > any token that is on line 3, col 5

    tracker.get_token(gaze=g)
    # > Token that is associated with gaze 'gaze'
```

You can mix and match all the different selectors.

### Getting all gazes in an edit window
```python

tracker.get_gazes_in_window(start_edit, end_edit)
# > all gazes in the given edit window
```
