# A-H target augmentation audit

Every run set now contains 18 target–instruction pairs. Existing validated targets were preserved; additional targets were selected from retained non-pink cards whose color–shape–count signature is unique within that map. Each added target has two nearby valid landmarks and paired easy/hard instructions.

| Run set | Ground cards | Original valid targets | Added targets | Current targets | Added card IDs |
|---|---:|---:|---:|---:|---|
| A | 59 | 8 | 10 | 18 | 6, 56, 54, 73, 19, 57, 64, 74, 49, 89 |
| B | 60 | 9 | 9 | 18 | 5, 1, 39, 44, 10, 20, 25, 27, 32 |
| C | 56 | 8 | 10 | 18 | 9, 10, 1, 87, 6, 25, 3, 17, 43, 93 |
| D | 52 | 6 | 12 | 18 | 49, 7, 25, 95, 33, 63, 68, 74, 22, 5, 23, 57 |
| E | 59 | 8 | 10 | 18 | 18, 33, 55, 60, 88, 15, 31, 45, 28, 38 |
| F | 59 | 7 | 11 | 18 | 55, 4, 60, 20, 6, 32, 80, 90, 99, 96, 19 |
| G | 57 | 8 | 10 | 18 | 15, 37, 16, 74, 89, 98, 3, 12, 27, 59 |
| H | 53 | 10 | 8 | 18 | 6, 77, 84, 28, 30, 44, 60, 98 |

## Validation

- All 64 condition files contain 18 target groups and 18 matching objectives.
- Every generated target survives the runtime material filter.
- Added card signatures are unique within their run-set map.
- Each stored landmark distance was recomputed and verified.
- Environment variants share identical target IDs and landmark chains.
- Easy and hard instructions remain paired with the same target card.
- All eight scanner condition schedules resolve successfully.

## Run set A

Targets increased from 8 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 59 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 6 | 2 black triangle | (11, 5) | rock at distance 1; short blue house at distance 1 |
| 56 | 1 blue plus | (9, 10) | rock at distance 1; tall blue house at distance 1 |
| 54 | 3 red heart | (0, 2) | lamppost at distance 1; rock at distance 1 |
| 73 | 3 orange triangle | (8, 7) | short blue house at distance 1; rock at distance 1 |
| 19 | 1 red heart | (2, 10) | tall grey house at distance 1; short grey house at distance 1 |
| 57 | 1 red square | (4, 6) | short blue house at distance 1; tall blue house at distance 1 |
| 64 | 3 yellow triangle | (7, 11) | rock at distance 1; tall blue house at distance 2 |
| 74 | 2 black square | (5, 10) | rock at distance 1; short yellow house at distance 1 |
| 49 | 2 red triangle | (3, 1) | rock at distance 2; lamppost at distance 1 |
| 89 | 2 blue triangle | (8, 3) | rock at distance 4; short blue house at distance 1 |

### Generated instructions

#### Card 6

- Easy: Find the card with two black triangles that is beside a rock that is beside a short blue house.
- Hard: Find the card with two black triangles that a rock that is beside a short blue house is beside.

#### Card 56

- Easy: Find the card with one blue plus that is next to a rock that is beside a tall blue house.
- Hard: Find the card with one blue plus that a rock that is beside a tall blue house is next to.

#### Card 54

- Easy: Find the card with three red hearts that is next to a lamppost that is beside a rock.
- Hard: Find the card with three red hearts that a lamppost that is beside a rock is next to.

#### Card 73

- Easy: Find the card with three orange triangles that is beside a short blue house that is next to a rock.
- Hard: Find the card with three orange triangles that a short blue house that is next to a rock is beside.

#### Card 19

- Easy: Find the card with one red heart that is next to a tall grey house that is beside a short grey house.
- Hard: Find the card with one red heart that a tall grey house that is beside a short grey house is next to.

#### Card 57

- Easy: Find the card with one red square that is beside a short blue house that is beside a tall blue house.
- Hard: Find the card with one red square that a short blue house that is beside a tall blue house is beside.

#### Card 64

- Easy: Find the card with three yellow triangles that is beside a rock that is 2 tiles from a tall blue house.
- Hard: Find the card with three yellow triangles that a rock that is 2 tiles from a tall blue house is beside.

#### Card 74

- Easy: Find the card with two black squares that is next to a rock that is next to a short yellow house.
- Hard: Find the card with two black squares that a rock that is next to a short yellow house is next to.

#### Card 49

- Easy: Find the card with two red triangles that is 2 tiles from a rock that is beside a lamppost.
- Hard: Find the card with two red triangles that a rock that is beside a lamppost is 2 tiles from.

#### Card 89

- Easy: Find the card with two blue triangles that is 4 tiles from a rock that is next to a short blue house.
- Hard: Find the card with two blue triangles that a rock that is next to a short blue house is 4 tiles from.

## Run set B

Targets increased from 9 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 60 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 5 | 3 green torus | (8, 2) | short grey house at distance 1; short yellow house at distance 1 |
| 1 | 1 blue triangle | (7, 5) | short yellow house at distance 1; tall grey house at distance 1 |
| 39 | 2 blue diamond | (7, 10) | rock at distance 1; tall red house at distance 3 |
| 44 | 2 yellow diamond | (3, 10) | short grey house at distance 2; tall blue house at distance 1 |
| 10 | 2 orange triangle | (9, 5) | short green house at distance 1; short yellow house at distance 1 |
| 20 | 1 yellow diamond | (10, 7) | short green house at distance 1; short yellow house at distance 1 |
| 25 | 1 orange diamond | (6, 7) | short yellow house at distance 1; tall grey house at distance 1 |
| 27 | 2 black square | (6, 4) | tall grey house at distance 1; short yellow house at distance 2 |
| 32 | 2 green plus | (6, 2) | tall grey house at distance 1; short yellow house at distance 2 |

### Generated instructions

#### Card 5

- Easy: Find the card with three green circles that is next to a short grey house that is beside a short yellow house.
- Hard: Find the card with three green circles that a short grey house that is beside a short yellow house is next to.

#### Card 1

- Easy: Find the card with one blue triangle that is next to a short yellow house that is next to a tall grey house.
- Hard: Find the card with one blue triangle that a short yellow house that is next to a tall grey house is next to.

#### Card 39

- Easy: Find the card with two blue diamonds that is next to a rock that is 3 tiles from a tall red house.
- Hard: Find the card with two blue diamonds that a rock that is 3 tiles from a tall red house is next to.

#### Card 44

- Easy: Find the card with two yellow diamonds that is 2 tiles from a short grey house that is next to a tall blue house.
- Hard: Find the card with two yellow diamonds that a short grey house that is next to a tall blue house is 2 tiles from.

#### Card 10

- Easy: Find the card with two orange triangles that is next to a short green house that is next to a short yellow house.
- Hard: Find the card with two orange triangles that a short green house that is next to a short yellow house is next to.

#### Card 20

- Easy: Find the card with one yellow diamond that is beside a short green house that is next to a short yellow house.
- Hard: Find the card with one yellow diamond that a short green house that is next to a short yellow house is beside.

#### Card 25

- Easy: Find the card with one orange diamond that is beside a short yellow house that is next to a tall grey house.
- Hard: Find the card with one orange diamond that a short yellow house that is next to a tall grey house is beside.

#### Card 27

- Easy: Find the card with two black squares that is next to a tall grey house that is 2 tiles from a short yellow house.
- Hard: Find the card with two black squares that a tall grey house that is 2 tiles from a short yellow house is next to.

#### Card 32

- Easy: Find the card with two green plusses that is beside a tall grey house that is 2 tiles from a short yellow house.
- Hard: Find the card with two green plusses that a tall grey house that is 2 tiles from a short yellow house is beside.

## Run set C

Targets increased from 8 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 56 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 9 | 3 black torus | (1, 11) | tree at distance 1; lamppost at distance 2 |
| 10 | 1 orange diamond | (10, 1) | lamppost at distance 1; short blue house at distance 2 |
| 1 | 1 blue diamond | (5, 11) | lamppost at distance 1; rock at distance 1 |
| 87 | 3 blue plus | (7, 5) | short red house at distance 1; short green house at distance 1 |
| 6 | 1 red star | (7, 1) | short blue house at distance 2; short grey house at distance 1 |
| 25 | 2 black plus | (11, 3) | lamppost at distance 2; short blue house at distance 2 |
| 3 | 3 blue torus | (1, 2) | short yellow house at distance 1; short blue house at distance 3 |
| 17 | 2 green torus | (3, 5) | short green house at distance 1; short blue house at distance 2 |
| 43 | 2 yellow triangle | (7, 9) | short yellow house at distance 1; short green house at distance 1 |
| 93 | 3 yellow torus | (1, 9) | short blue house at distance 1; tree at distance 3 |

### Generated instructions

#### Card 9

- Easy: Find the card with three black circles that is beside a tree that is 2 tiles from a lamppost.
- Hard: Find the card with three black circles that a tree that is 2 tiles from a lamppost is beside.

#### Card 10

- Easy: Find the card with one orange diamond that is next to a lamppost that is 2 tiles from a short blue house.
- Hard: Find the card with one orange diamond that a lamppost that is 2 tiles from a short blue house is next to.

#### Card 1

- Easy: Find the card with one blue diamond that is next to a lamppost that is next to a rock.
- Hard: Find the card with one blue diamond that a lamppost that is next to a rock is next to.

#### Card 87

- Easy: Find the card with three blue plusses that is next to a short red house that is beside a short green house.
- Hard: Find the card with three blue plusses that a short red house that is beside a short green house is next to.

#### Card 6

- Easy: Find the card with one red star that is 2 tiles from a short blue house that is beside a short grey house.
- Hard: Find the card with one red star that a short blue house that is beside a short grey house is 2 tiles from.

#### Card 25

- Easy: Find the card with two black plusses that is 2 tiles from a lamppost that is 2 tiles from a short blue house.
- Hard: Find the card with two black plusses that a lamppost that is 2 tiles from a short blue house is 2 tiles from.

#### Card 3

- Easy: Find the card with three blue circles that is next to a short yellow house that is 3 tiles from a short blue house.
- Hard: Find the card with three blue circles that a short yellow house that is 3 tiles from a short blue house is next to.

#### Card 17

- Easy: Find the card with two green circles that is beside a short green house that is 2 tiles from a short blue house.
- Hard: Find the card with two green circles that a short green house that is 2 tiles from a short blue house is beside.

#### Card 43

- Easy: Find the card with two yellow triangles that is beside a short yellow house that is beside a short green house.
- Hard: Find the card with two yellow triangles that a short yellow house that is beside a short green house is beside.

#### Card 93

- Easy: Find the card with three yellow circles that is beside a short blue house that is 3 tiles from a tree.
- Hard: Find the card with three yellow circles that a short blue house that is 3 tiles from a tree is beside.

## Run set D

Targets increased from 6 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 52 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 49 | 1 yellow heart | (11, 11) | short grey house at distance 4; tall red house at distance 1 |
| 7 | 1 blue plus | (10, 5) | lamppost at distance 2; rock at distance 1 |
| 25 | 1 red plus | (7, 1) | short grey house at distance 2; lamppost at distance 1 |
| 95 | 3 blue heart | (7, 9) | rock at distance 1; tall blue house at distance 1 |
| 33 | 2 black square | (9, 7) | tall grey house at distance 1; tall red house at distance 2 |
| 63 | 2 black heart | (1, 2) | short blue house at distance 1; short yellow house at distance 2 |
| 68 | 3 orange square | (2, 4) | short yellow house at distance 1; short red house at distance 1 |
| 74 | 1 black heart | (4, 9) | short green house at distance 1; tall blue house at distance 1 |
| 22 | 3 yellow square | (11, 8) | tall red house at distance 2; short grey house at distance 1 |
| 5 | 1 blue diamond | (1, 0) | tall blue house at distance 1; short red house at distance 1 |
| 23 | 2 black plus | (6, 2) | tall blue house at distance 1; short grey house at distance 3 |
| 57 | 3 orange plus | (9, 5) | tall grey house at distance 1; tall red house at distance 2 |

### Generated instructions

#### Card 49

- Easy: Find the card with one yellow heart that is 4 tiles from a short grey house that is beside a tall red house.
- Hard: Find the card with one yellow heart that a short grey house that is beside a tall red house is 4 tiles from.

#### Card 7

- Easy: Find the card with one blue plus that is 2 tiles from a lamppost that is next to a rock.
- Hard: Find the card with one blue plus that a lamppost that is next to a rock is 2 tiles from.

#### Card 25

- Easy: Find the card with one red plus that is 2 tiles from a short grey house that is beside a lamppost.
- Hard: Find the card with one red plus that a short grey house that is beside a lamppost is 2 tiles from.

#### Card 95

- Easy: Find the card with three blue hearts that is beside a rock that is beside a tall blue house.
- Hard: Find the card with three blue hearts that a rock that is beside a tall blue house is beside.

#### Card 33

- Easy: Find the card with two black squares that is beside a tall grey house that is 2 tiles from a tall red house.
- Hard: Find the card with two black squares that a tall grey house that is 2 tiles from a tall red house is beside.

#### Card 63

- Easy: Find the card with two black hearts that is next to a short blue house that is 2 tiles from a short yellow house.
- Hard: Find the card with two black hearts that a short blue house that is 2 tiles from a short yellow house is next to.

#### Card 68

- Easy: Find the card with three orange squares that is beside a short yellow house that is next to a short red house.
- Hard: Find the card with three orange squares that a short yellow house that is next to a short red house is beside.

#### Card 74

- Easy: Find the card with one black heart that is next to a short green house that is next to a tall blue house.
- Hard: Find the card with one black heart that a short green house that is next to a tall blue house is next to.

#### Card 22

- Easy: Find the card with three yellow squares that is 2 tiles from a tall red house that is next to a short grey house.
- Hard: Find the card with three yellow squares that a tall red house that is next to a short grey house is 2 tiles from.

#### Card 5

- Easy: Find the card with one blue diamond that is beside a tall blue house that is beside a short red house.
- Hard: Find the card with one blue diamond that a tall blue house that is beside a short red house is beside.

#### Card 23

- Easy: Find the card with two black plusses that is beside a tall blue house that is 3 tiles from a short grey house.
- Hard: Find the card with two black plusses that a tall blue house that is 3 tiles from a short grey house is beside.

#### Card 57

- Easy: Find the card with three orange plusses that is next to a tall grey house that is 2 tiles from a tall red house.
- Hard: Find the card with three orange plusses that a tall grey house that is 2 tiles from a tall red house is next to.

## Run set E

Targets increased from 8 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 59 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 18 | 3 yellow plus | (6, 1) | short blue house at distance 1; short red house at distance 3 |
| 33 | 1 green heart | (0, 11) | short red house at distance 2; short grey house at distance 2 |
| 55 | 3 red star | (8, 1) | short red house at distance 1; rock at distance 3 |
| 60 | 2 blue heart | (2, 7) | short red house at distance 1; tall blue house at distance 2 |
| 88 | 1 blue square | (1, 9) | short grey house at distance 1; lamppost at distance 1 |
| 15 | 3 orange heart | (6, 5) | short yellow house at distance 2; tall blue house at distance 2 |
| 31 | 1 red triangle | (11, 3) | rock at distance 2; tree at distance 1 |
| 45 | 2 yellow plus | (0, 0) | rock at distance 2; short blue house at distance 4 |
| 28 | 2 blue torus | (5, 11) | lamppost at distance 3; short grey house at distance 1 |
| 38 | 2 red heart | (3, 3) | rock at distance 3; short blue house at distance 4 |

### Generated instructions

#### Card 18

- Easy: Find the card with three yellow plusses that is next to a short blue house that is 3 tiles from a short red house.
- Hard: Find the card with three yellow plusses that a short blue house that is 3 tiles from a short red house is next to.

#### Card 33

- Easy: Find the card with one green heart that is 2 tiles from a short red house that is 2 tiles from a short grey house.
- Hard: Find the card with one green heart that a short red house that is 2 tiles from a short grey house is 2 tiles from.

#### Card 55

- Easy: Find the card with three red stars that is next to a short red house that is 3 tiles from a rock.
- Hard: Find the card with three red stars that a short red house that is 3 tiles from a rock is next to.

#### Card 60

- Easy: Find the card with two blue hearts that is beside a short red house that is 2 tiles from a tall blue house.
- Hard: Find the card with two blue hearts that a short red house that is 2 tiles from a tall blue house is beside.

#### Card 88

- Easy: Find the card with one blue square that is beside a short grey house that is next to a lamppost.
- Hard: Find the card with one blue square that a short grey house that is next to a lamppost is beside.

#### Card 15

- Easy: Find the card with three orange hearts that is 2 tiles from a short yellow house that is 2 tiles from a tall blue house.
- Hard: Find the card with three orange hearts that a short yellow house that is 2 tiles from a tall blue house is 2 tiles from.

#### Card 31

- Easy: Find the card with one red triangle that is 2 tiles from a rock that is next to a tree.
- Hard: Find the card with one red triangle that a rock that is next to a tree is 2 tiles from.

#### Card 45

- Easy: Find the card with two yellow plusses that is 2 tiles from a rock that is 4 tiles from a short blue house.
- Hard: Find the card with two yellow plusses that a rock that is 4 tiles from a short blue house is 2 tiles from.

#### Card 28

- Easy: Find the card with two blue circles that is 3 tiles from a lamppost that is next to a short grey house.
- Hard: Find the card with two blue circles that a lamppost that is next to a short grey house is 3 tiles from.

#### Card 38

- Easy: Find the card with two red hearts that is 3 tiles from a rock that is 4 tiles from a short blue house.
- Hard: Find the card with two red hearts that a rock that is 4 tiles from a short blue house is 3 tiles from.

## Run set F

Targets increased from 7 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 59 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 55 | 3 red triangle | (1, 5) | lamppost at distance 1; short yellow house at distance 3 |
| 4 | 3 orange triangle | (9, 10) | rock at distance 1; short yellow house at distance 1 |
| 60 | 1 black torus | (1, 11) | lamppost at distance 4; short green house at distance 1 |
| 20 | 3 black square | (5, 5) | short red house at distance 1; short yellow house at distance 1 |
| 6 | 3 green heart | (11, 9) | lamppost at distance 1; rock at distance 3 |
| 32 | 3 black star | (2, 4) | lamppost at distance 1; short yellow house at distance 3 |
| 80 | 3 red star | (9, 7) | short blue house at distance 1; short yellow house at distance 1 |
| 90 | 1 blue star | (6, 4) | tree at distance 1; short red house at distance 2 |
| 99 | 1 black square | (1, 2) | short yellow house at distance 1; lamppost at distance 3 |
| 96 | 1 yellow triangle | (2, 9) | lamppost at distance 3; short green house at distance 1 |
| 19 | 2 blue triangle | (7, 8) | short green house at distance 1; lamppost at distance 1 |

### Generated instructions

#### Card 55

- Easy: Find the card with three red triangles that is next to a lamppost that is 3 tiles from a short yellow house.
- Hard: Find the card with three red triangles that a lamppost that is 3 tiles from a short yellow house is next to.

#### Card 4

- Easy: Find the card with three orange triangles that is next to a rock that is beside a short yellow house.
- Hard: Find the card with three orange triangles that a rock that is beside a short yellow house is next to.

#### Card 60

- Easy: Find the card with one black circle that is 4 tiles from a lamppost that is beside a short green house.
- Hard: Find the card with one black circle that a lamppost that is beside a short green house is 4 tiles from.

#### Card 20

- Easy: Find the card with three black squares that is next to a short red house that is beside a short yellow house.
- Hard: Find the card with three black squares that a short red house that is beside a short yellow house is next to.

#### Card 6

- Easy: Find the card with three green hearts that is beside a lamppost that is 3 tiles from a rock.
- Hard: Find the card with three green hearts that a lamppost that is 3 tiles from a rock is beside.

#### Card 32

- Easy: Find the card with three black stars that is beside a lamppost that is 3 tiles from a short yellow house.
- Hard: Find the card with three black stars that a lamppost that is 3 tiles from a short yellow house is beside.

#### Card 80

- Easy: Find the card with three red stars that is beside a short blue house that is next to a short yellow house.
- Hard: Find the card with three red stars that a short blue house that is next to a short yellow house is beside.

#### Card 90

- Easy: Find the card with one blue star that is next to a tree that is 2 tiles from a short red house.
- Hard: Find the card with one blue star that a tree that is 2 tiles from a short red house is next to.

#### Card 99

- Easy: Find the card with one black square that is beside a short yellow house that is 3 tiles from a lamppost.
- Hard: Find the card with one black square that a short yellow house that is 3 tiles from a lamppost is beside.

#### Card 96

- Easy: Find the card with one yellow triangle that is 3 tiles from a lamppost that is beside a short green house.
- Hard: Find the card with one yellow triangle that a lamppost that is beside a short green house is 3 tiles from.

#### Card 19

- Easy: Find the card with two blue triangles that is next to a short green house that is next to a lamppost.
- Hard: Find the card with two blue triangles that a short green house that is next to a lamppost is next to.

## Run set G

Targets increased from 8 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 57 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 15 | 1 black heart | (0, 2) | tall red house at distance 1; rock at distance 3 |
| 37 | 1 orange heart | (3, 5) | rock at distance 1; short yellow house at distance 2 |
| 16 | 2 yellow diamond | (1, 11) | rock at distance 1; short green house at distance 2 |
| 74 | 2 red heart | (7, 10) | rock at distance 2; short green house at distance 1 |
| 89 | 2 green heart | (11, 9) | short yellow house at distance 2; tall grey house at distance 1 |
| 98 | 2 black torus | (11, 2) | short red house at distance 3; short grey house at distance 1 |
| 3 | 1 green triangle | (7, 3) | short blue house at distance 1; short green house at distance 1 |
| 12 | 3 black torus | (2, 10) | rock at distance 1; short green house at distance 2 |
| 27 | 3 green heart | (1, 5) | short grey house at distance 1; short yellow house at distance 2 |
| 59 | 3 black plus | (1, 0) | short red house at distance 1; tall red house at distance 3 |

### Generated instructions

#### Card 15

- Easy: Find the card with one black heart that is beside a tall red house that is 3 tiles from a rock.
- Hard: Find the card with one black heart that a tall red house that is 3 tiles from a rock is beside.

#### Card 37

- Easy: Find the card with one orange heart that is next to a rock that is 2 tiles from a short yellow house.
- Hard: Find the card with one orange heart that a rock that is 2 tiles from a short yellow house is next to.

#### Card 16

- Easy: Find the card with two yellow diamonds that is next to a rock that is 2 tiles from a short green house.
- Hard: Find the card with two yellow diamonds that a rock that is 2 tiles from a short green house is next to.

#### Card 74

- Easy: Find the card with two red hearts that is 2 tiles from a rock that is beside a short green house.
- Hard: Find the card with two red hearts that a rock that is beside a short green house is 2 tiles from.

#### Card 89

- Easy: Find the card with two green hearts that is 2 tiles from a short yellow house that is beside a tall grey house.
- Hard: Find the card with two green hearts that a short yellow house that is beside a tall grey house is 2 tiles from.

#### Card 98

- Easy: Find the card with two black circles that is 3 tiles from a short red house that is next to a short grey house.
- Hard: Find the card with two black circles that a short red house that is next to a short grey house is 3 tiles from.

#### Card 3

- Easy: Find the card with one green triangle that is beside a short blue house that is next to a short green house.
- Hard: Find the card with one green triangle that a short blue house that is next to a short green house is beside.

#### Card 12

- Easy: Find the card with three black circles that is beside a rock that is 2 tiles from a short green house.
- Hard: Find the card with three black circles that a rock that is 2 tiles from a short green house is beside.

#### Card 27

- Easy: Find the card with three green hearts that is beside a short grey house that is 2 tiles from a short yellow house.
- Hard: Find the card with three green hearts that a short grey house that is 2 tiles from a short yellow house is beside.

#### Card 59

- Easy: Find the card with three black plusses that is beside a short red house that is 3 tiles from a tall red house.
- Hard: Find the card with three black plusses that a short red house that is 3 tiles from a tall red house is beside.

## Run set H

Targets increased from 10 to 18 without changing the 12x12 map or any card appearance.

Every added target has a color-shape-count signature that occurs only once among the 53 retained cards. Two nearby non-pink landmarks were assigned to each target, and matched easy/hard instructions were generated with identical lexical choices.

| Card ID | Card | Cell | Landmark chain |
|---:|---|---|---|
| 6 | 1 green heart | (6, 4) | lamppost at distance 1; tree at distance 1 |
| 77 | 3 green heart | (5, 11) | tree at distance 1; rock at distance 2 |
| 84 | 1 green torus | (9, 10) | rock at distance 1; tall blue house at distance 1 |
| 28 | 3 yellow heart | (10, 3) | lamppost at distance 3; short red house at distance 4 |
| 30 | 2 yellow heart | (4, 3) | short red house at distance 1; tall blue house at distance 1 |
| 44 | 2 yellow plus | (4, 8) | short yellow house at distance 1; rock at distance 1 |
| 60 | 2 black triangle | (2, 2) | short red house at distance 1; tall blue house at distance 1 |
| 98 | 2 red square | (3, 11) | tree at distance 1; rock at distance 2 |

### Generated instructions

#### Card 6

- Easy: Find the card with one green heart that is next to a lamppost that is next to a tree.
- Hard: Find the card with one green heart that a lamppost that is next to a tree is next to.

#### Card 77

- Easy: Find the card with three green hearts that is next to a tree that is 2 tiles from a rock.
- Hard: Find the card with three green hearts that a tree that is 2 tiles from a rock is next to.

#### Card 84

- Easy: Find the card with one green circle that is beside a rock that is beside a tall blue house.
- Hard: Find the card with one green circle that a rock that is beside a tall blue house is beside.

#### Card 28

- Easy: Find the card with three yellow hearts that is 3 tiles from a lamppost that is 4 tiles from a short red house.
- Hard: Find the card with three yellow hearts that a lamppost that is 4 tiles from a short red house is 3 tiles from.

#### Card 30

- Easy: Find the card with two yellow hearts that is beside a short red house that is beside a tall blue house.
- Hard: Find the card with two yellow hearts that a short red house that is beside a tall blue house is beside.

#### Card 44

- Easy: Find the card with two yellow plusses that is next to a short yellow house that is beside a rock.
- Hard: Find the card with two yellow plusses that a short yellow house that is beside a rock is next to.

#### Card 60

- Easy: Find the card with two black triangles that is beside a short red house that is beside a tall blue house.
- Hard: Find the card with two black triangles that a short red house that is beside a tall blue house is beside.

#### Card 98

- Easy: Find the card with two red squares that is beside a tree that is 2 tiles from a rock.
- Hard: Find the card with two red squares that a tree that is 2 tiles from a rock is beside.
