# Static data folder

## /training

This text file, `training`, includes examples of "Would you rather"
questions with some limited markup.  These examples are
used to train a natural language model to find the
choices posed by a would you rather question.  Choices are
marked using two level of curly brackets `{}`.  The outer
brackets indicate choices that a dumb algorithm should be
fairly able to identify; inner brackets indicate more
ideal answers that would require a higher level of semantic
understanding to identify.  For example, this is a possible
training example:

```
Would you rather {pet {a dog}} or {{a cat}}.
```

The first option, at the dumb level, is `pet a dog` although 
because there's no verb in the second option, a human will
assume the second choice is "pet a cat" and reasonable answers
might be just "dog" or "cat".

Right now we're probably not being consistent with whether we
include articles like "a" or "the", in the future we might
go up to 3 levels of brackets to make things a bit better.