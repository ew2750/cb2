# Current scenario 001: 12x12 material audit

This report describes the scenario-001 materials currently used by the task.

- Run sets A-D and G-H use their original scenario 001 layouts.
- Run sets E and F use their original scenario 003 layouts, promoted and renamed to scenario 001.
- All current materials are native 12x12 maps.
- Cards outside the retained bounds and all pink cards are removed.
- Former pink-house cells use `GROUND_TILE_PATH` (asset ID 28) and no longer function as landmarks.
- Instructions are discarded when their target card or a required landmark is unavailable.
- Every run set has been augmented to 18 targets. Current target details are in `ALL_RUNSETS_TARGET_AUGMENTATION_AUDIT.md`.

| Current run set/scenario | Original source | Cards retained | Current targets |
|---|---|---:|---:|
| A/001 | A/001 | 59 | 18 |
| B/001 | B/001 | 60 | 18 |
| C/001 | C/001 | 56 | 18 |
| D/001 | D/001 | 52 | 18 |
| E/001 | E/003 | 59 | 18 |
| F/001 | F/003 | 59 | 18 |
| G/001 | G/001 | 57 | 18 |
| H/001 | H/001 | 53 | 18 |

## runset_A / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 40
- Pink cards inside retained bounds: 3
- Cards retained: 59
- Former pink-house cells converted to path: 1
- Original instruction-target pairs retained after filtering: 8 of 18
- Additional generated instruction-target pairs: 10
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 1: 1 orange torus, offset cell (11, 14)
- ID 3: 1 blue heart, offset cell (13, 14)
- ID 5: 1 pink diamond, offset cell (13, 0)
- ID 8: 2 red square, offset cell (11, 12)
- ID 9: 1 green diamond, offset cell (13, 9)
- ID 11: 1 blue torus, offset cell (10, 13)
- ID 14: 2 blue plus, offset cell (14, 11)
- ID 17: 1 red square, offset cell (2, 14)
- ID 18: 2 orange heart, offset cell (8, 13)
- ID 20: 3 blue diamond, offset cell (13, 3)
- ID 23: 2 green square, offset cell (0, 12)
- ID 25: 2 orange torus, offset cell (5, 12)
- ID 27: 2 orange heart, offset cell (0, 14)
- ID 28: 2 red square, offset cell (14, 1)
- ID 29: 1 blue heart, offset cell (3, 14)
- ID 30: 1 red diamond, offset cell (5, 13)
- ID 32: 1 blue diamond, offset cell (13, 10)
- ID 33: 2 blue plus, offset cell (14, 12)
- ID 34: 1 blue star, offset cell (10, 12)
- ID 35: 1 black plus, offset cell (12, 12)
- ID 37: 1 red star, offset cell (14, 10)
- ID 38: 1 green diamond, offset cell (12, 11)
- ID 41: 1 red square, offset cell (14, 14)
- ID 43: 1 red diamond, offset cell (13, 11)
- ID 44: 1 pink diamond, offset cell (2, 12)
- ID 48: 2 green diamond, offset cell (4, 12)
- ID 55: 1 pink diamond, offset cell (12, 9)
- ID 60: 2 orange plus, offset cell (7, 13)
- ID 61: 2 green plus, offset cell (6, 12)
- ID 66: 3 yellow torus, offset cell (6, 13)
- ID 68: 1 black heart, offset cell (7, 12)
- ID 71: 1 green square, offset cell (9, 14)
- ID 77: 1 orange heart, offset cell (9, 13)
- ID 79: 2 orange heart, offset cell (9, 12)
- ID 81: 1 green diamond, offset cell (13, 7)
- ID 82: 1 blue heart, offset cell (1, 14)
- ID 86: 2 green plus, offset cell (8, 12)
- ID 93: 1 red square, offset cell (3, 13)
- ID 96: 2 orange torus, offset cell (12, 14)
- ID 99: 1 orange heart, offset cell (12, 0)

### Pink cards removed inside the map

- ID 7: 1 pink heart, offset cell (8, 0)
- ID 75: 2 pink star, offset cell (1, 5)
- ID 84: 1 pink diamond, offset cell (1, 11)

### Former pink-house cells converted to path

- Offset cell (8, 6)

### Instruction-target pairs discarded

- Target [3] — target card removed: [3]. Instruction: Find the card with one blue heart that is 2 tiles from a rock that is 3 tiles from a tree.
- Target [61] — target card removed: [61]. Instruction: Find the card with two green plusses that is 2 tiles from a tree that is 2 tiles from a rock.
- Target [25] — target card removed: [25]. Instruction: Find the card with two orange circles that is 2 tiles from a rock that is next to a lamppost.
- Target [35] — target card removed: [35]. Instruction: Find the card with one black plus that is 2 tiles from a rock that is 2 tiles from a tree.
- Target [18] — target card removed: [18]. Instruction: Find the card with two orange hearts that is 2 tiles from a tree that is next to a lamppost.
- Target [17] — target card removed: [17]. Instruction: Find the card with one red square that is 4 tiles from a tree that is 2 tiles from a tall grey house.
- Target [38] — target card removed: [38]. Instruction: Find the card with one green diamond that is next to a rock that is 3 tiles from a lamppost.
- Target [14] — target card removed: [14]. Instruction: Find the card with two blue plusses that is 4 tiles from a rock that is 3 tiles from a tree.
- Target [55] — target card removed: [55]. Instruction: Find the card with one pink diamond that is next to a rock that is 3 tiles from a short blue house.
- Target [69] — required landmark removed or excluded. Instruction: Find the card with one green star that is 3 tiles from a tree that is beside a rock.

## runset_B / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 34
- Pink cards inside retained bounds: 8
- Cards retained: 60
- Former pink-house cells converted to path: 0
- Original instruction-target pairs retained after filtering: 9 of 18
- Additional generated instruction-target pairs: 9
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 4: 2 blue star, offset cell (14, 7)
- ID 7: 1 green plus, offset cell (9, 12)
- ID 9: 2 pink diamond, offset cell (13, 0)
- ID 11: 2 green square, offset cell (7, 12)
- ID 12: 2 blue heart, offset cell (13, 6)
- ID 16: 1 red diamond, offset cell (3, 13)
- ID 19: 1 green torus, offset cell (13, 11)
- ID 23: 1 pink diamond, offset cell (3, 14)
- ID 29: 1 black torus, offset cell (0, 13)
- ID 31: 2 red diamond, offset cell (12, 14)
- ID 34: 2 blue heart, offset cell (14, 9)
- ID 35: 3 yellow plus, offset cell (12, 4)
- ID 40: 2 pink diamond, offset cell (2, 12)
- ID 43: 2 green square, offset cell (7, 13)
- ID 45: 2 orange torus, offset cell (13, 1)
- ID 47: 2 pink torus, offset cell (13, 3)
- ID 49: 2 green diamond, offset cell (11, 12)
- ID 50: 2 orange torus, offset cell (13, 14)
- ID 52: 1 blue plus, offset cell (12, 13)
- ID 53: 2 green square, offset cell (1, 12)
- ID 55: 1 green torus, offset cell (14, 6)
- ID 60: 1 green torus, offset cell (0, 14)
- ID 67: 1 pink star, offset cell (14, 14)
- ID 69: 1 black triangle, offset cell (10, 13)
- ID 70: 1 orange star, offset cell (14, 11)
- ID 72: 3 yellow square, offset cell (1, 13)
- ID 74: 2 green plus, offset cell (14, 2)
- ID 79: 3 orange diamond, offset cell (12, 1)
- ID 82: 3 black diamond, offset cell (4, 12)
- ID 83: 1 green torus, offset cell (13, 8)
- ID 92: 2 black star, offset cell (5, 12)
- ID 93: 2 orange heart, offset cell (13, 9)
- ID 94: 1 black torus, offset cell (13, 4)
- ID 101: 1 red diamond, offset cell (14, 3)

### Pink cards removed inside the map

- ID 0: 2 pink diamond, offset cell (5, 5)
- ID 3: 2 pink torus, offset cell (7, 9)
- ID 6: 2 pink torus, offset cell (11, 2)
- ID 54: 2 pink torus, offset cell (3, 7)
- ID 66: 2 pink diamond, offset cell (10, 5)
- ID 78: 1 pink diamond, offset cell (2, 7)
- ID 84: 1 pink diamond, offset cell (0, 4)
- ID 89: 1 pink diamond, offset cell (10, 2)

### Former pink-house cells converted to path

- None

### Instruction-target pairs discarded

- Target [66] — target card removed: [66]. Instruction: Find the card with two pink diamonds that is 2 tiles from a short green house that is next to a short yellow house.
- Target [4] — target card removed: [4]. Instruction: Find the card with two blue stars that is 2 tiles from a tree that is 3 tiles from a short green house.
- Target [67] — target card removed: [67]. Instruction: Find the card with one pink star that is 2 tiles from a rock that is beside a tree.
- Target [6] — target card removed: [6]. Instruction: Find the card with two pink circles that is next to a tree that is 3 tiles from a short red house.
- Target [89] — target card removed: [89]. Instruction: Find the card with one pink diamond that is 2 tiles from a short yellow house that is 3 tiles from a short grey house.
- Target [45] — target card removed: [45]. Instruction: Find the card with two orange circles that is 4 tiles from a short red house that is next to a short grey house.
- Target [81] — required landmark removed or excluded. Instruction: Find the card with two orange hearts that is 2 tiles from a tree that is next to a rock.
- Target [60] — target card removed: [60]. Instruction: Find the card with one green circle that is 2 tiles from a rock that is 3 tiles from another rock.
- Target [16] — target card removed: [16]. Instruction: Find the card with one red diamond that is next to a rock that is 4 tiles from a tree.

## runset_C / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 33
- Pink cards inside retained bounds: 13
- Cards retained: 56
- Former pink-house cells converted to path: 2
- Original instruction-target pairs retained after filtering: 8 of 18
- Additional generated instruction-target pairs: 10
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 0: 1 orange plus, offset cell (2, 12)
- ID 2: 1 red diamond, offset cell (7, 13)
- ID 5: 2 yellow plus, offset cell (14, 9)
- ID 7: 2 green heart, offset cell (14, 2)
- ID 11: 2 pink square, offset cell (4, 13)
- ID 16: 1 black plus, offset cell (7, 14)
- ID 24: 1 black torus, offset cell (3, 14)
- ID 30: 2 pink plus, offset cell (1, 13)
- ID 37: 2 orange plus, offset cell (12, 7)
- ID 42: 1 blue square, offset cell (10, 13)
- ID 47: 2 orange plus, offset cell (11, 12)
- ID 50: 1 blue diamond, offset cell (12, 9)
- ID 52: 2 orange plus, offset cell (7, 12)
- ID 53: 2 pink square, offset cell (14, 8)
- ID 54: 1 orange plus, offset cell (13, 1)
- ID 55: 1 pink triangle, offset cell (14, 10)
- ID 56: 1 red heart, offset cell (12, 3)
- ID 57: 1 red square, offset cell (12, 1)
- ID 60: 1 red heart, offset cell (13, 4)
- ID 64: 2 green torus, offset cell (5, 14)
- ID 65: 1 black square, offset cell (13, 0)
- ID 66: 1 blue square, offset cell (14, 13)
- ID 69: 2 orange torus, offset cell (13, 5)
- ID 72: 1 pink square, offset cell (4, 14)
- ID 77: 2 green star, offset cell (2, 14)
- ID 79: 1 red plus, offset cell (0, 13)
- ID 86: 2 pink diamond, offset cell (12, 0)
- ID 91: 1 red plus, offset cell (14, 14)
- ID 92: 2 green square, offset cell (10, 12)
- ID 95: 2 black heart, offset cell (10, 14)
- ID 97: 2 green torus, offset cell (5, 13)
- ID 99: 2 red diamond, offset cell (11, 13)
- ID 101: 2 green torus, offset cell (14, 7)

### Pink cards removed inside the map

- ID 18: 1 pink torus, offset cell (9, 1)
- ID 20: 2 pink star, offset cell (5, 3)
- ID 22: 1 pink torus, offset cell (5, 5)
- ID 26: 2 pink plus, offset cell (2, 7)
- ID 27: 2 pink diamond, offset cell (8, 2)
- ID 28: 2 pink plus, offset cell (2, 8)
- ID 31: 2 pink torus, offset cell (3, 1)
- ID 33: 2 pink diamond, offset cell (11, 0)
- ID 34: 1 pink torus, offset cell (5, 9)
- ID 35: 2 pink star, offset cell (9, 3)
- ID 71: 2 pink diamond, offset cell (3, 10)
- ID 76: 1 pink torus, offset cell (11, 2)
- ID 82: 2 pink plus, offset cell (0, 2)

### Former pink-house cells converted to path

- Offset cell (2, 9)
- Offset cell (3, 8)

### Instruction-target pairs discarded

- Target [37] — target card removed: [37]. Instruction: Find the card with two orange plusses that is beside a lamppost that is beside a rock.
- Target [18] — target card removed: [18]. Instruction: Find the card with one pink circle that is beside a tall blue house that is 2 tiles from a lamppost.
- Target [83] — required landmark removed or excluded. Instruction: Find the card with one green circle that is 2 tiles from a rock that is 2 tiles from a tree.
- Target [15] — required landmark removed or excluded. Instruction: Find the card with one black circle that is next to a short blue house that is 2 tiles from a short pink house.
- Target [97] — target card removed: [97]. Instruction: Find the card with two green circles that is 3 tiles from a lamppost that is beside a rock.
- Target [90] — required landmark removed or excluded. Instruction: Find the card with one black square that is 2 tiles from a short blue house that is 3 tiles from a rock.
- Target [82] — target card removed: [82]. Instruction: Find the card with two pink plusses that is beside a short yellow house that is 2 tiles from another short yellow house.
- Target [16] — target card removed: [16]. Instruction: Find the card with one black plus that is 2 tiles from a rock that is 3 tiles from a tree.
- Target [71] — target card removed: [71]. Instruction: Find the card with two pink diamonds that is beside a tree that is 2 tiles from a rock.
- Target [84] — required landmark removed or excluded. Instruction: Find the card with one orange plus that is beside a lamppost that is beside a tree.

## runset_D / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 34
- Pink cards inside retained bounds: 16
- Cards retained: 52
- Former pink-house cells converted to path: 4
- Original instruction-target pairs retained after filtering: 6 of 18
- Additional generated instruction-target pairs: 12
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 2: 1 pink heart, offset cell (10, 14)
- ID 3: 2 green star, offset cell (12, 5)
- ID 4: 1 blue plus, offset cell (9, 13)
- ID 6: 1 black torus, offset cell (6, 13)
- ID 12: 1 pink triangle, offset cell (12, 4)
- ID 15: 2 green square, offset cell (13, 3)
- ID 16: 2 yellow star, offset cell (12, 1)
- ID 26: 2 red square, offset cell (14, 6)
- ID 27: 2 red heart, offset cell (14, 5)
- ID 29: 2 red heart, offset cell (2, 13)
- ID 32: 1 blue plus, offset cell (14, 4)
- ID 34: 1 green plus, offset cell (13, 9)
- ID 36: 1 black plus, offset cell (12, 11)
- ID 37: 1 green diamond, offset cell (14, 14)
- ID 39: 2 red heart, offset cell (3, 13)
- ID 40: 1 black plus, offset cell (11, 14)
- ID 43: 1 orange torus, offset cell (14, 7)
- ID 48: 2 green star, offset cell (9, 12)
- ID 50: 3 orange plus, offset cell (13, 0)
- ID 51: 2 pink heart, offset cell (1, 14)
- ID 52: 2 pink square, offset cell (14, 8)
- ID 56: 2 blue star, offset cell (13, 7)
- ID 59: 2 green plus, offset cell (9, 14)
- ID 61: 2 green square, offset cell (13, 10)
- ID 62: 1 pink square, offset cell (13, 4)
- ID 64: 3 red square, offset cell (5, 14)
- ID 65: 1 red square, offset cell (11, 13)
- ID 67: 2 green plus, offset cell (13, 6)
- ID 77: 1 black torus, offset cell (13, 1)
- ID 87: 2 black star, offset cell (4, 13)
- ID 88: 1 blue plus, offset cell (2, 14)
- ID 90: 2 blue star, offset cell (12, 10)
- ID 96: 1 pink plus, offset cell (13, 14)
- ID 101: 1 orange torus, offset cell (0, 13)

### Pink cards removed inside the map

- ID 9: 1 pink star, offset cell (6, 4)
- ID 10: 2 pink heart, offset cell (4, 8)
- ID 11: 2 pink square, offset cell (5, 3)
- ID 13: 1 pink plus, offset cell (0, 7)
- ID 28: 1 pink heart, offset cell (10, 10)
- ID 31: 1 pink heart, offset cell (3, 1)
- ID 35: 3 pink triangle, offset cell (0, 4)
- ID 41: 2 pink heart, offset cell (4, 10)
- ID 44: 1 pink plus, offset cell (2, 7)
- ID 45: 1 pink plus, offset cell (2, 2)
- ID 46: 2 pink heart, offset cell (4, 5)
- ID 58: 2 pink square, offset cell (9, 4)
- ID 69: 2 pink square, offset cell (5, 4)
- ID 81: 1 pink heart, offset cell (0, 10)
- ID 86: 2 pink diamond, offset cell (0, 5)
- ID 100: 3 pink diamond, offset cell (7, 6)

### Former pink-house cells converted to path

- Offset cell (0, 0)
- Offset cell (0, 6)
- Offset cell (8, 3)
- Offset cell (8, 6)

### Instruction-target pairs discarded

- Target [70] — required landmark removed or excluded. Instruction: Find the card with two red squares that is 2 tiles from a lamppost that is 2 tiles from a rock.
- Target [27] — target card removed: [27]. Instruction: Find the card with two red hearts that is 4 tiles from a lamppost that is beside a short grey house.
- Target [43] — target card removed: [43]. Instruction: Find the card with one orange circle that is 5 tiles from a tall grey house that is 2 tiles from a tall red house.
- Target [32] — target card removed: [32]. Instruction: Find the card with one blue plus that is 4 tiles from a lamppost that is beside a rock.
- Target [81] — target card removed: [81]. Instruction: Find the card with one pink heart that is 4 tiles from a tree that is 5 tiles from a tall grey house.
- Target [1] — required landmark removed or excluded. Instruction: Find the card with two blue stars that is 2 tiles from a tall red house that is 2 tiles from a short pink house.
- Target [65] — target card removed: [65]. Instruction: Find the card with one red square that is next to a rock that is 2 tiles from a lamppost.
- Target [44] — target card removed: [44]. Instruction: Find the card with one pink plus that is 2 tiles from a short grey house that is 3 tiles from a short red house.
- Target [58] — target card removed: [58]. Instruction: Find the card with two pink squares that is 2 tiles from a short pink house that is next to a short grey house.
- Target [34] — target card removed: [34]. Instruction: Find the card with one green plus that is beside a rock that is 5 tiles from another rock.
- Target [51] — target card removed: [51]. Instruction: Find the card with two pink hearts that is next to a tree that is 7 tiles from a rock.
- Target [37] — target card removed: [37]. Instruction: Find the card with one green diamond that is 4 tiles from a rock that is 3 tiles from a lamppost.

## runset_E / scenario 001

- Original source layout: scenario 003
- Original cards: 102
- Cards outside 12x12 bounds: 32
- Pink cards inside retained bounds: 11
- Cards retained: 59
- Former pink-house cells converted to path: 3
- Original instruction-target pairs retained after filtering: 8 of 18
- Additional generated instruction-target pairs: 10
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 0: 3 blue heart, offset cell (13, 14)
- ID 4: 2 green heart, offset cell (0, 14)
- ID 5: 2 orange square, offset cell (10, 13)
- ID 7: 1 red diamond, offset cell (12, 3)
- ID 8: 1 orange torus, offset cell (4, 13)
- ID 9: 2 green heart, offset cell (5, 12)
- ID 11: 2 pink heart, offset cell (13, 4)
- ID 14: 3 orange star, offset cell (14, 0)
- ID 16: 2 green plus, offset cell (13, 3)
- ID 19: 2 black diamond, offset cell (10, 14)
- ID 22: 2 red plus, offset cell (3, 14)
- ID 26: 2 black torus, offset cell (6, 12)
- ID 37: 1 red diamond, offset cell (1, 12)
- ID 39: 1 pink star, offset cell (12, 11)
- ID 40: 1 blue heart, offset cell (12, 7)
- ID 42: 1 orange plus, offset cell (9, 14)
- ID 51: 2 pink heart, offset cell (0, 13)
- ID 52: 1 orange torus, offset cell (9, 13)
- ID 56: 2 red plus, offset cell (12, 12)
- ID 58: 2 green diamond, offset cell (12, 1)
- ID 61: 2 black torus, offset cell (13, 5)
- ID 62: 1 black star, offset cell (12, 10)
- ID 65: 1 black star, offset cell (11, 13)
- ID 69: 2 yellow triangle, offset cell (14, 5)
- ID 71: 3 green star, offset cell (13, 0)
- ID 74: 1 black diamond, offset cell (11, 14)
- ID 75: 1 orange torus, offset cell (12, 4)
- ID 77: 1 black torus, offset cell (14, 14)
- ID 86: 1 red square, offset cell (7, 13)
- ID 96: 1 black diamond, offset cell (4, 12)
- ID 98: 1 orange heart, offset cell (12, 9)
- ID 100: 1 blue heart, offset cell (13, 9)

### Pink cards removed inside the map

- ID 13: 2 pink star, offset cell (5, 6)
- ID 17: 1 pink torus, offset cell (1, 8)
- ID 25: 1 pink star, offset cell (0, 2)
- ID 41: 2 pink star, offset cell (9, 5)
- ID 44: 3 pink plus, offset cell (11, 7)
- ID 64: 1 pink star, offset cell (11, 9)
- ID 66: 2 pink heart, offset cell (1, 2)
- ID 84: 1 pink star, offset cell (8, 11)
- ID 90: 2 pink heart, offset cell (0, 5)
- ID 91: 2 pink star, offset cell (3, 2)
- ID 93: 2 pink star, offset cell (5, 9)

### Former pink-house cells converted to path

- Offset cell (5, 2)
- Offset cell (6, 0)
- Offset cell (9, 0)

### Instruction-target pairs discarded

- Target [83] — required landmark removed or excluded. Instruction: Find the card with two orange plusses that is 4 tiles from a tree that is 5 tiles from a rock.
- Target [91] — target card removed: [91]. Instruction: Find the card with two pink stars that is 2 tiles from a rock that is 4 tiles from a short pink house.
- Target [25] — target card removed: [25]. Instruction: Find the card with one pink star that is 5 tiles from a short red house that is beside another short red house.
- Target [90] — target card removed: [90]. Instruction: Find the card with two pink hearts that is beside a tall blue house that is 2 tiles from a short red house.
- Target [67] — required landmark removed or excluded. Instruction: Find the card with one red square that is 4 tiles from a tree that is 7 tiles from a rock.
- Target [7] — target card removed: [7]. Instruction: Find the card with one red diamond that is beside a tree that is 2 tiles from a rock.
- Target [58] — target card removed: [58]. Instruction: Find the card with two green diamonds that is beside a tree that is next to another tree.
- Target [42] — target card removed: [42]. Instruction: Find the card with one orange plus that is 2 tiles from a rock that is 6 tiles from a lamppost.
- Target [62] — target card removed: [62]. Instruction: Find the card with one black star that is 3 tiles from a rock that is 3 tiles from another rock.
- Target [63] — required landmark removed or excluded. Instruction: Find the card with one orange heart that is next to a short pink house that is beside a short yellow house.

## runset_F / scenario 001

- Original source layout: scenario 003
- Original cards: 102
- Cards outside 12x12 bounds: 33
- Pink cards inside retained bounds: 10
- Cards retained: 59
- Former pink-house cells converted to path: 1
- Original instruction-target pairs retained after filtering: 7 of 18
- Additional generated instruction-target pairs: 11
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 2: 2 green star, offset cell (7, 12)
- ID 3: 2 orange diamond, offset cell (4, 12)
- ID 5: 2 orange torus, offset cell (1, 12)
- ID 8: 2 pink heart, offset cell (13, 13)
- ID 9: 1 orange heart, offset cell (14, 11)
- ID 15: 2 blue star, offset cell (11, 14)
- ID 16: 2 red star, offset cell (9, 12)
- ID 17: 2 red plus, offset cell (4, 14)
- ID 24: 3 red star, offset cell (11, 12)
- ID 25: 1 pink torus, offset cell (5, 12)
- ID 30: 1 pink square, offset cell (14, 9)
- ID 35: 2 orange plus, offset cell (12, 5)
- ID 36: 1 blue square, offset cell (12, 7)
- ID 37: 2 orange heart, offset cell (2, 13)
- ID 45: 2 orange diamond, offset cell (4, 13)
- ID 49: 3 yellow star, offset cell (6, 12)
- ID 50: 1 green square, offset cell (12, 1)
- ID 56: 2 red star, offset cell (0, 14)
- ID 58: 2 pink plus, offset cell (6, 14)
- ID 64: 2 black diamond, offset cell (0, 12)
- ID 65: 2 pink heart, offset cell (7, 14)
- ID 69: 2 orange heart, offset cell (13, 1)
- ID 70: 1 red square, offset cell (12, 9)
- ID 72: 1 orange heart, offset cell (10, 13)
- ID 75: 3 black triangle, offset cell (13, 6)
- ID 76: 1 blue plus, offset cell (13, 11)
- ID 78: 2 green plus, offset cell (12, 8)
- ID 79: 2 pink torus, offset cell (13, 14)
- ID 84: 2 black diamond, offset cell (13, 4)
- ID 87: 2 pink plus, offset cell (13, 8)
- ID 92: 2 orange torus, offset cell (11, 13)
- ID 97: 2 orange star, offset cell (13, 0)
- ID 101: 1 red square, offset cell (12, 12)

### Pink cards removed inside the map

- ID 0: 2 pink plus, offset cell (6, 2)
- ID 22: 2 pink torus, offset cell (9, 3)
- ID 23: 2 pink plus, offset cell (4, 11)
- ID 26: 2 pink torus, offset cell (1, 3)
- ID 53: 2 pink heart, offset cell (0, 1)
- ID 57: 2 pink heart, offset cell (7, 5)
- ID 61: 1 pink plus, offset cell (10, 4)
- ID 74: 2 pink torus, offset cell (8, 4)
- ID 83: 1 pink diamond, offset cell (6, 5)
- ID 85: 1 pink torus, offset cell (11, 6)

### Former pink-house cells converted to path

- Offset cell (8, 6)

### Instruction-target pairs discarded

- Target [78] — target card removed: [78]. Instruction: Find the card with two green plusses that is 2 tiles from a lamppost that is 5 tiles from a short red house.
- Target [15] — target card removed: [15]. Instruction: Find the card with two blue stars that is 3 tiles from a lamppost that is 2 tiles from a rock.
- Target [79] — target card removed: [79]. Instruction: Find the card with two pink circles that is 2 tiles from a tree that is beside a rock.
- Target [97] — target card removed: [97]. Instruction: Find the card with two orange stars that is next to a lamppost that is 3 tiles from a rock.
- Target [36] — target card removed: [36]. Instruction: Find the card with one blue square that is 2 tiles from a lamppost that is 4 tiles from another lamppost.
- Target [65] — target card removed: [65]. Instruction: Find the card with two pink hearts that is 2 tiles from a rock that is next to another rock.
- Target [16] — target card removed: [16]. Instruction: Find the card with two red stars that is beside a lamppost that is 2 tiles from another lamppost.
- Target [42] — required landmark removed or excluded. Instruction: Find the card with two black hearts that is 5 tiles from a rock that is 3 tiles from another rock.
- Target [3] — target card removed: [3]. Instruction: Find the card with two orange diamonds that is 3 tiles from a rock that is 2 tiles from a tree.
- Target [5] — target card removed: [5]. Instruction: Find the card with two orange circles that is beside a rock that is 3 tiles from another rock.
- Target [23] — target card removed: [23]. Instruction: Find the card with two pink plusses that is 2 tiles from a rock that is 3 tiles from another rock.

## runset_G / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 36
- Pink cards inside retained bounds: 9
- Cards retained: 57
- Former pink-house cells converted to path: 4
- Original instruction-target pairs retained after filtering: 8 of 18
- Additional generated instruction-target pairs: 10
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 4: 1 green star, offset cell (14, 1)
- ID 5: 2 yellow heart, offset cell (0, 12)
- ID 7: 2 blue square, offset cell (14, 7)
- ID 10: 2 green triangle, offset cell (12, 7)
- ID 17: 3 blue torus, offset cell (14, 5)
- ID 19: 2 green triangle, offset cell (13, 8)
- ID 20: 1 orange diamond, offset cell (12, 11)
- ID 23: 1 green plus, offset cell (14, 12)
- ID 24: 1 green heart, offset cell (11, 14)
- ID 26: 1 black star, offset cell (13, 13)
- ID 31: 1 black star, offset cell (2, 14)
- ID 32: 2 blue plus, offset cell (14, 9)
- ID 33: 2 blue star, offset cell (12, 12)
- ID 34: 1 yellow star, offset cell (14, 14)
- ID 36: 3 black triangle, offset cell (14, 11)
- ID 39: 3 orange plus, offset cell (13, 6)
- ID 40: 1 pink plus, offset cell (7, 12)
- ID 41: 2 blue star, offset cell (14, 8)
- ID 47: 1 blue plus, offset cell (4, 13)
- ID 53: 2 blue diamond, offset cell (8, 12)
- ID 56: 1 red plus, offset cell (6, 14)
- ID 58: 1 red star, offset cell (14, 6)
- ID 60: 2 orange torus, offset cell (9, 12)
- ID 61: 1 red diamond, offset cell (12, 0)
- ID 62: 1 green diamond, offset cell (12, 13)
- ID 63: 1 orange diamond, offset cell (11, 13)
- ID 65: 1 red star, offset cell (13, 12)
- ID 70: 1 red plus, offset cell (12, 1)
- ID 75: 1 blue heart, offset cell (13, 3)
- ID 81: 1 pink plus, offset cell (12, 8)
- ID 83: 2 blue triangle, offset cell (10, 14)
- ID 86: 2 green plus, offset cell (13, 5)
- ID 88: 1 black plus, offset cell (13, 0)
- ID 92: 1 pink diamond, offset cell (10, 13)
- ID 97: 1 pink plus, offset cell (8, 13)
- ID 99: 1 black plus, offset cell (4, 12)

### Pink cards removed inside the map

- ID 9: 1 pink square, offset cell (8, 11)
- ID 25: 2 pink star, offset cell (1, 4)
- ID 29: 2 pink star, offset cell (8, 5)
- ID 35: 2 pink star, offset cell (5, 4)
- ID 46: 3 pink triangle, offset cell (5, 10)
- ID 54: 2 pink star, offset cell (10, 2)
- ID 79: 2 pink square, offset cell (0, 4)
- ID 93: 1 pink square, offset cell (6, 7)
- ID 100: 1 pink plus, offset cell (8, 1)

### Former pink-house cells converted to path

- Offset cell (3, 2)
- Offset cell (5, 0)
- Offset cell (6, 0)
- Offset cell (6, 6)

### Instruction-target pairs discarded

- Target [7] — target card removed: [7]. Instruction: Find the card with two blue squares that is 3 tiles from a tree that is 3 tiles from another tree.
- Target [35] — target card removed: [35]. Instruction: Find the card with two pink stars that is 2 tiles from a short green house that is 2 tiles from a short pink house.
- Target [58] — target card removed: [58]. Instruction: Find the card with one red star that is 2 tiles from a tree that is 3 tiles from another tree.
- Target [47] — target card removed: [47]. Instruction: Find the card with one blue plus that is beside a tree that is 2 tiles from a rock.
- Target [99] — target card removed: [99]. Instruction: Find the card with one black plus that is 2 tiles from a rock that is 3 tiles from a tall red house.
- Target [81] — target card removed: [81]. Instruction: Find the card with one pink plus that is 3 tiles from a short yellow house that is 2 tiles from a tree.
- Target [56] — target card removed: [56]. Instruction: Find the card with one red plus that is 2 tiles from a tree that is next to another tree.
- Target [20] — target card removed: [20]. Instruction: Find the card with one orange diamond that is 4 tiles from a tall grey house that is 3 tiles from a rock.
- Target [77] — required landmark removed or excluded. Instruction: Find the card with two blue diamonds that is beside a rock that is 3 tiles from another rock.
- Target [33] — target card removed: [33]. Instruction: Find the card with two blue stars that is 3 tiles from a tree that is next to a rock.

## runset_H / scenario 001

- Original source layout: scenario 001
- Original cards: 102
- Cards outside 12x12 bounds: 38
- Pink cards inside retained bounds: 11
- Cards retained: 53
- Former pink-house cells converted to path: 1
- Original instruction-target pairs retained after filtering: 10 of 18
- Additional generated instruction-target pairs: 8
- Current instruction-target pairs: 18

### Cards outside the 12x12 map

- ID 0: 3 green diamond, offset cell (4, 14)
- ID 3: 1 red diamond, offset cell (12, 4)
- ID 8: 1 blue diamond, offset cell (11, 13)
- ID 10: 3 black star, offset cell (8, 12)
- ID 11: 1 orange square, offset cell (3, 13)
- ID 12: 1 yellow torus, offset cell (0, 12)
- ID 13: 1 orange square, offset cell (9, 12)
- ID 14: 1 orange heart, offset cell (12, 12)
- ID 16: 1 black square, offset cell (13, 2)
- ID 17: 1 green torus, offset cell (1, 13)
- ID 19: 2 pink torus, offset cell (2, 12)
- ID 21: 2 black diamond, offset cell (7, 14)
- ID 26: 1 orange heart, offset cell (6, 12)
- ID 31: 1 blue diamond, offset cell (12, 9)
- ID 32: 3 pink square, offset cell (14, 4)
- ID 36: 1 green torus, offset cell (12, 8)
- ID 37: 1 green diamond, offset cell (13, 0)
- ID 42: 1 red triangle, offset cell (12, 13)
- ID 43: 1 orange heart, offset cell (12, 2)
- ID 45: 2 red heart, offset cell (14, 13)
- ID 47: 1 blue star, offset cell (6, 14)
- ID 49: 2 red triangle, offset cell (8, 14)
- ID 52: 1 pink square, offset cell (6, 13)
- ID 55: 2 orange plus, offset cell (1, 12)
- ID 56: 2 blue torus, offset cell (2, 13)
- ID 58: 1 green torus, offset cell (5, 13)
- ID 63: 3 green heart, offset cell (12, 14)
- ID 66: 1 red diamond, offset cell (14, 12)
- ID 67: 1 orange square, offset cell (13, 5)
- ID 70: 1 pink square, offset cell (3, 14)
- ID 71: 2 black diamond, offset cell (13, 13)
- ID 73: 1 orange plus, offset cell (8, 13)
- ID 79: 1 orange heart, offset cell (10, 12)
- ID 81: 2 blue heart, offset cell (13, 8)
- ID 83: 3 blue star, offset cell (10, 13)
- ID 86: 2 yellow plus, offset cell (7, 13)
- ID 89: 2 black heart, offset cell (13, 9)
- ID 97: 1 black square, offset cell (12, 0)

### Pink cards removed inside the map

- ID 15: 2 pink torus, offset cell (1, 0)
- ID 22: 2 pink heart, offset cell (5, 3)
- ID 27: 2 pink heart, offset cell (3, 10)
- ID 51: 2 pink heart, offset cell (10, 6)
- ID 53: 2 pink heart, offset cell (10, 1)
- ID 59: 1 pink square, offset cell (11, 2)
- ID 62: 2 pink heart, offset cell (1, 6)
- ID 69: 2 pink heart, offset cell (1, 2)
- ID 75: 1 pink square, offset cell (6, 2)
- ID 80: 2 pink square, offset cell (4, 0)
- ID 85: 2 pink heart, offset cell (0, 1)

### Former pink-house cells converted to path

- Offset cell (5, 6)

### Instruction-target pairs discarded

- Target [56] — target card removed: [56]. Instruction: Find the card with two blue circles that is 3 tiles from a tree that is 2 tiles from another tree.
- Target [19] — target card removed: [19]. Instruction: Find the card with two pink circles that is next to a tree that is 3 tiles from another tree.
- Target [51] — target card removed: [51]. Instruction: Find the card with two pink hearts that is 2 tiles from a short grey house that is beside a short green house.
- Target [97] — target card removed: [97]. Instruction: Find the card with one black square that is 3 tiles from a tree that is 3 tiles from a lamppost.
- Target [81] — target card removed: [81]. Instruction: Find the card with two blue hearts that is 2 tiles from a rock that is 2 tiles from a short green house.
- Target [79] — target card removed: [79]. Instruction: Find the card with one orange heart that is 3 tiles from a rock that is next to a tree.
- Target [75] — target card removed: [75]. Instruction: Find the card with one pink square that is next to a streetlight that is next to a lamppost.
- Target [36] — target card removed: [36]. Instruction: Find the card with one green circle that is 3 tiles from a short green house that is 2 tiles from a tall grey house.
