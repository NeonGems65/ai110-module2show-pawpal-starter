# PawPal+ Project Reflection


## 1. System Design

Three Core Actions
- Add a pet
- Schedule Walks
- See Today's Tasks

**a. Initial design**
Classes: 

Owner - identifying info and a list of pets with appropriate methods
    Methods - Create pet
    Attributes - list of pets, The times that owner is available


Pet - create task for pet
    Methods - Add task, list tasks, manage tasks 
    Attributes - description, due date, completion status


Task - holds information about a task
    Methods - mark_complete 
    Attributes - Description, due time, completion status, one relavent method 


Scheduler - responsible for scheduling tasks
    retrieves, organizes, or manages tasks across multiple pets (not just one pet's tasks, and not merely holding data) 

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.
    In the UML, added two new wrapper classes to keep the data more organized instead of stored in a tuple

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
