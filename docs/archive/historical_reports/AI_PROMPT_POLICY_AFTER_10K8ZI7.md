# AI Prompt Policy After 10K8ZI7

Prompt metadata validation is local-only.

Required fields:
- `prompt_name`
- `purpose`

Rejected conditions:
- external execution enabled
- live network enabled
- training enabled
- prompt secrets enabled

Policy result:
- no prompt execution
- no model execution
- no credential reads
- no network access

