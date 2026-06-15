# Leader arm and bimanual notes

## Can the leader arm be driven?

Yes, but treat it differently from the follower:

- The leader has motors and encoders.
- The SO-101 leader uses different gear ratios so it can support itself and remain easy to move.
- Recent SO-101 docs/tutorials mention leader tracking of the follower for human intervention workflows.

For a high-school workshop, the safest use is still:

> student moves leader by hand -> follower mirrors it

If you demo leader tracking/follower tracking, keep hands away from the leader handle while software is driving it.

## Bimanual recording idea

For real bimanual manipulation, use two manipulation followers, ideally two leader/follower pairs:

> left leader -> left follower  
> right leader -> right follower

The leader alone is not a great second working arm for object manipulation because its mechanics/end-effector are optimized for teleoperation input, not robust object interaction.

## High-school version

Use bimanual only as a wow demo:

- Two followers pass a soft foam cube.
- Or one arm holds a cup while the other drops a foam ball.
- Keep it fully scripted or teacher-operated.

Do not make bimanual recording part of the first 3-hour student activity.
