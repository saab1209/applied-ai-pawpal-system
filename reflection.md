# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

### 1a. Initial design
* **Three Core User Actions:**
  1. Register one or more pets (`Pet`) under a household profile (`Owner`).
  2. Add, view, and mark pet care routines (`Task`—such as feedings, walks, medications, and vet appointments) as complete.
  3. View a prioritized daily schedule sorted by time or urgency while automatically detecting overlapping time conflicts.
* **Chosen Classes & Responsibilities:**
  * `Owner`: Stores owner profile details and manages a list of `Pet` objects.
  * `Pet`: Stores pet metadata (`name`, `species`, `age`) and owns its list of care `Task` items.
  * `Task`: Uses a Python `@dataclass` to hold task attributes (`title`, `category`, `time`, `duration_minutes`, `priority`, `frequency`, `completed`, `pet_name`) and handles completion/recurrence logic.
  * `Scheduler`: Acts as the algorithmic engine over an `Owner`'s pets—sorting tasks chronologically or by priority, filtering by pet/status, and detecting time-window collisions.

### 1b. Design changes
* After reviewing the initial class skeleton, I added `pet_name` and `duration_minutes` directly onto the `Task` dataclass and separated `Scheduler` from `Owner`. Storing `pet_name` and `duration_minutes` on each `Task` makes cross-pet sorting and exact time-overlap detection (`start_time` to `start_time + duration_minutes`) much cleaner without needing nested lookups during scheduling.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

* **Considered Constraints:** The scheduler evaluates scheduled start time (`"HH:MM"`), task duration (`duration_minutes`), urgency (`High`, `Medium`, `Low`), recurrence frequency (`Once`, `Daily`, `Weekly`), pet ownership (`pet_name`), and completion status (`pending` vs. `completed`).
* **How Priorities Were Decided:** Chronological start time and overlapping duration windows mattered most because pet routines—especially medications and feedings—are time-sensitive and a single owner cannot physically handle two active tasks at once. Priority level (`High` > `Medium` > `Low`) serves as the secondary sorting tie-breaker so urgent medical care always surfaces first when viewing by urgency.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

* **Scheduler Tradeoff:** `Scheduler.detect_conflicts()` flags any two incomplete tasks across the entire household whose `[start, start + duration_minutes)` time windows overlap, even if they belong to different pets or involve passive tasks.
* **Why This Tradeoff Is Reasonable:** For a single pet owner managing daily routines at home, treating all overlapping time windows as potential collisions prevents missed medications or double-booked walks—making conservative conflict warnings far safer than allowing silent schedule overlaps.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
