- **Don't** Repeatedly write a Tactics, Techniques and Procedures (TTP) pattern
  in different endpoint detection and response (EDR) query languages.

- **Do** Express all patterns in a common language so that it can be compiled to
  different EDR queries and Security Information and Event Management (SIEM)
  APIs.

- **Don't** Repeatedly write dependent hunting steps such as getting child
  processes for suspicious processes against various record/log formats in
  different parts of a hunt.

- **Do** Express flows of hunting steps in a common means that can be reused
  and re-executed at different parts of a hunt or even in different hunts.

- **Don't** Repeatedly write different execution-environment adapters for an
  implemented domain-specific detection module or a proprietary detection box.

- **Do** Express analytics execution with uniform input/output schema and
  encapsulating existing analytics to operate in a reusable manner.

Reading carefully, you will find the examples of repeats are actually not
literally repeating. Each repeat is a little different from its
siblings due to their different execution environments. We need to take it a
little bit further to find what is repeated and how to not repeat ourselves.
