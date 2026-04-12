
##  Colour Palette

| Variable | Hex | Used For |
|---|---|---|
| `--bg` | `#faf7f2` | Page background (warm off-white) |
| `--surface` | `#ffffff` | Cards, task items, rows |
| `--surface2` | `#f5f0e8` | Input backgrounds, badges |
| `--border` | `#e8dfd0` | All borders and dividers |
| `--accent` | `#c17f5a` | Primary brand colour (terracotta/rust) |
| `--accent2` | `#8a9e7a` | Secondary (sage green, used for success) |
| `--text` | `#3d342a` | Main body text |
| `--muted` | `#9e8e7e` | Placeholder text, labels, secondary copy |
| `--danger` | `#c0604a` | Errors, delete hover |
| `--success` | `#8a9e7a` | Completed task checkmark |

**Leaderboard-specific colours:**
| Rank | Hex |
|---|---|
| 🥇 Gold | `#c49a2a` |
| 🥈 Silver | `#9e9087` |
| 🥉 Bronze | `#b07248` |

---

## 🔤 Typography

### Font Families
| Font | Type | Used For |
|---|---|---|
| [Playfair Display](https://fonts.google.com/specimen/Playfair+Display) | Serif | Headings, titles, brand name, scores |
| [Nunito](https://fonts.google.com/specimen/Nunito) | Sans-serif | All body text, buttons, labels |

### Font Sizes
| Element | Size |
|---|---|
| Brand name | `22px` |
| Login title | `30px` |
| Greeting title | `32px` |
| Leaderboard title | `32px` |
| Body / task text | `15px` |
| Input text | `14px` |
| Labels, hints, tags | `12px–13px` |
| Badge / stat labels | `11px–12px` |
| Form labels | `12px` (uppercase) |

---

## 🔄 Emoji → Icon Changes

All emojis have been replaced with [Lucide Icons](https://lucide.dev/) loaded via CDN.

| Was | Now (Lucide) |
|---|---|
| 🏡 | `home` |
| 🧹 Cleaning | `sparkles` |
| 🍳 Kitchen | `utensils` |
| 🌿 Garden | `leaf` |
| ✓ Done | `check-circle` |
| 🏆 Leaderboard | `trophy` |
| 📋 Other | `clipboard-list` |
| 🛋️ Empty state | `sofa` |
| → Arrow | `arrow-right` |
| ✕ Delete | `x` |

---

##  File Structure

```
homely/
├── index.html     # Main HTML structure
├── styles.css     # All styles and CSS variables
└── app.js         # JavaScript logic
```


## ✨ Features

- ✅ Login system with multiple users
- ✅ Add, complete and delete household tasks
- ✅ Auto category detection (cleaning, kitchen, garden)
- ✅ Filter tasks by category
- ✅ Leaderboard with podium display
- ✅ Time-based greeting (morning / afternoon / evening)
- ✅ Lucide icons throughout
