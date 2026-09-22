# departure_board

An airport departure board on a 1208x552 canvas, built entirely from
segment displays: six flights with time, destination, flight number, gate
and a colored status, a title and a clock. There is no `assets/` folder:
no images, no fonts, nothing to license.

| Part | How it works |
| --- | --- |
| Every text on the board | `digits` layers with an `alpha14` segment display; the dark segments are the display's `unlit` color |
| Row contents | `text` bindings on text variables: `dest_3`, `gate_3`, ... The host decides which flight is in which row |
| Times and the clock | `06.40`: a `.` lights the dot of the cell before it, so a time takes four cells |
| Status color | a segment display has one `fill`, so the status is three `digits` layers (amber, green, red) bound to the same variable, each in a group whose `opacity` is a mapped binding on the status: `BOARDING` shows the green one, `DELAYED` and `CANCELLED` the red one |
| Blinking `BOARDING` | an `autoplay`, `loop` timeline on the green layer; the group around it carries the binding, because a running timeline would override a binding on the same layer |
| Refresh fade | each row is an `unlit` group of dark displays with `"text": ""` under a `lit` group of the bound displays without `unlit`. The `lit` group has one timeline with `"trigger": ["refresh", "row_3"]` that fades its digits in: the host fades a row when it changes what the row shows, or the whole board with `refresh`, and the dark segments stay put |

It needs cuelight `main` with timelines that take a list of triggers
(cuelight #26).

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/departure_board
```

`test-driver.json` is picked up automatically and plays two hours at a
small airport in a minute: flights move from `ON TIME` over `GATE OPEN`,
`BOARDING` and `CLOSING` to `DEPARTED` and leave the board, one is delayed
and gets a new time, one is cancelled. A flight that leaves the board
leaves its row empty for a second; then the rows below move up one by
one and the next flight joins at the bottom. All of that is the host
setting variables and firing `row_N`: the show has no idea rows move. The schedule and the status rules
live in [`tools/departure_board_day.py`](../tools/departure_board_day.py),
which writes the driver; the show itself is a plain, regular document.
You can also set a cell from the player's prompt: `status_2=BOARDING`.

The destinations are real cities; airlines, flight numbers and times are
made up.

## What would make it better

- More digit displays: a 5x7 dot matrix and a split-flap style with a
  flip animation on change would make this board (and scoreboards,
  clocks, tickers) far more convincing than fourteen segments.
- A bindable `fill` on a segment display: the status would be one layer
  with a mapped color instead of three layers in three groups.
- A way to react to a variable changing (a timeline that plays when its
  layer's bound text changes): the host would not have to fire `row_3`
  next to setting `status_3`.
- Layer templates or repeaters: the six rows are the same 110 lines with
  another number in the variable names.
