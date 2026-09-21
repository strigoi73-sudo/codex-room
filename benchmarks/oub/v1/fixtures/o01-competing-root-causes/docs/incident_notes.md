# Incident notes

[N601] Customer support confirmed duplicate settled charges for `ord-A17` and `ord-B04`. No duplicate settled charge was reported for `ord-C09` or `ord-D12`.

[N602] On-call initially suspected the invoice database because pool-saturation warnings were visible later in the same dashboard window.

[N603] A second engineer suspected duplicate ingress because both affected orders show two gateway charge identifiers.

[N604] A third engineer suspected two workers simultaneously processing the same durable job because the worker service has parallelism greater than one.

Treat these as hypotheses and observations, not established causes.
