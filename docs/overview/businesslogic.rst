Threat hunting activities can be summarized by asking and answering two types of
questions:

- What to hunt?

    - What is the threat hypothesis?
    - What is the next step?
    - What threat intelligence should be added?
    - What machine learning models fit?

- How to hunt?

    - How to query this EDR?
    - How to extract the field for the next query?
    - How to enrich this data?
    - How to plug in this machine learning model?

Any threat hunting activity involves both types of questions and the answers
to both questions contain domain-specific knowledge. However, the types of domain
knowledge regarding these two types of questions are not the same. The answers
to the *what* contain the domain knowledge that is highly creative, mostly
abstract, and largely reusable from one hunt to another, while the answers to the
*how* guides the realization of the *what* and are replaced from one hunting
platform to another.

To not repeat ourselves, we need to identify and split the *what* and *how* for
all hunting steps and flows, and answer them separately -- the *what* will be
reused in different parts of a hunt or different hunts, while the *how* will be
developed to instantiate *what* regarding their different environments.

With the understanding of the two types of domain knowledge invoked in threat
hunting, we can start to reuse domain knowledge regarding the questions of
*what* and not repeat ourselves, yet we still need to answer the tremendous
amount of mundane questions of *how*, which is hunting platform-specific and
not repeatable. Can we go further?
