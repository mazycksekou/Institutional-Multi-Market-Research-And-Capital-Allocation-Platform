# NFL as a Sports Profile Instance

NFL is the first sports profile instance in the repository.

It is not a separate architecture.

It reuses the Sports market profile family so that future sports can follow the same contract shape.

## What NFL inherits

NFL inherits the Sports profile requirements for:

- league
- season
- event identifiers
- teams
- players
- markets
- odds snapshots
- results
- point-in-time timestamps
- feature groups
- validation rules
- leakage rules
- storage requirements
- backtest requirements

## What NFL adds

NFL adds sport-specific extensions such as:

- QB fields
- RB fields
- WR fields
- TE fields
- offensive line fields
- defensive line fields
- linebacker fields
- defensive back fields
- special teams fields
- coaching fields
- officials fields

## Why this matters

This keeps NFL useful as a first implementation while preventing the repository from creating a separate architecture for each sport.

Future sports should reuse the same Sports profile family and only add their own sport-specific extensions.
