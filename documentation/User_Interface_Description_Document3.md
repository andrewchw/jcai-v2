# User Interface Description Document: Microsoft Edge Chatbot Extension for Jira Action Item Management

## Layout Structure
- A floating, circular chatbot icon is fixed in the bottom-right corner of the Microsoft Edge browser, visible across all webpages, with dynamic margins (10px on 1366x768 screens, 20px on 1920x1080 screens) to avoid clipping.
- Clicking the icon toggles a 350px-wide sidebar on the right, sliding in with a 0.3s animation. The sidebar spans the full browser height and includes: a chat input at the bottom, a scrollable conversation history in the middle, and a sortable task list with evidence thumbnails at the top.
- The sidebar can be minimized by clicking the icon or resized by dragging a left-edge handle (250px to 450px), allowing user customization. When minimized, the icon remains semi-transparent to reduce distraction.

## Core Components
- **Chatbot Icon**: A 40px circular icon with a white clipboard-checkmark symbol on a Jira-blue (#0052CC) background. It bounces (0.5s animation) for new notifications and scales up 15% on hover.
- **Chat Sidebar**:
  - **Chat Input**: A single-line text field with a send button, supporting natural language commands (e.g., “Create task for Alice due Friday”).
  - **Conversation History**: A scrollable chat thread showing user inputs and bot responses, with embedded Jira issue links and timestamps.
  - **Task List**: A sortable list of up to 5 recent/open tasks, displaying issue ID, title, assignee, and due date with a color-coded SLA progress bar. Users can sort by due date or assignee via clickable headers. A toggle hides/shows the list for chat-only mode.
  - **Evidence Hub**: A 2x2 thumbnail grid for uploaded files, supporting drag-and-drop to attach to Jira issues, with clickable previews.
- **OAuth Login Button**: A “Log in with Jira” button in the sidebar on first use, triggering an OAuth 2.0 flow in a pop-up window.
- **Notifications**: 300x100px browser notifications appear above the icon (max 2 per minute), with reply buttons (e.g., “Done”, “Snooze”). Queued notifications display sequentially.

## Interaction Patterns
- **Toggling Sidebar**: Click the chatbot icon to open/close the sidebar or drag the resize handle to adjust width, with smooth transitions.
- **Natural Language Commands**: Type commands in the chat input (e.g., “Show my tasks”), with bot responses in the conversation history, powered by the sooperset/mcp-atlassian server and OpenRouter LLM.
- **Auto-Suggestions**: Chat input provides autocomplete for project IDs and assignees, using MCP server’s `jira_search` metadata.
- **Task Sorting**: Click task list headers (e.g., “Due Date”) to sort ascending/descending; toggle list visibility via a button.
- **Notifications**: Click “Done” on a reminder to trigger `jira_transition_issue` or “Snooze” to delay. Notifications auto-dismiss after 5s unless interacted with.
- **Evidence Upload**: Drag-and-drop files into the evidence hub, uploading to Jira via `jira_add_comment`, with thumbnails updating in real-time.
- **OAuth Login**: First-time users click the login button, authenticate via Jira OAuth, and credentials are saved for future sessions.

## Visual Design Elements & Color Scheme
- **Color Scheme**:
  - Primary: Jira Blue (#0052CC) for icon, buttons, and chat highlights.
  - Secondary: White (#FFFFFF) for sidebar and chat bubbles.
  - Accents: Bright Green (#00C4B4) for completed tasks, Soft Red (#FF7452) for overdue tasks, Light Gray (#DFE1E6) for borders and inactive elements.
- **Icon Design**: The clipboard-checkmark is bold and centered, with a bounce animation for notifications and a scale-up effect on hover.
- **Chat Styling**: User messages in right-aligned blue bubbles, bot responses in left-aligned white bubbles with gray borders.
- **Effects**: Sidebar has a subtle shadow (2px) for depth; task list rows highlight in light blue (#DEEBFF) on hover; notifications fade in/out.

## Mobile, Web App, Desktop Considerations
- **Desktop (Primary)**: Optimized for Edge on 15" laptops (1366x768) and 24" desktops (1920x1080). The 350px sidebar occupies ~25% of smaller screens, ~18% of larger ones, leaving space for webpages.
- **Mobile**: Not applicable per PRD, but the sidebar could adapt to a full-screen modal if mobile support is added later.
- **Web App**: Not applicable, as the solution is an extension. Intranet-hosted Python/MCP servers ensure firewall compliance.
- **Screen Size Adaptation**: Sidebar scales to 100% width below 1024px; icon margins adjust dynamically; task list font size reduces to 14px on smaller screens for readability.

## Typography
- **Font**: Roboto (Google Fonts), aligning with Jira’s professional style.
  - Chat Input/Responses: 14px, Regular.
  - Task List Titles: 16px, Medium.
  - Notifications: 14px, Bold.
  - Labels (e.g., due dates): 12px, Regular.
- **Line Spacing**: 1.5 for chat and task lists, ensuring clarity.
- **Alignment**: Left for bot responses and task details, right for user inputs.

## Accessibility
- **Keyboard Navigation**: Tab order: icon, chat input, task list headers, notification buttons. Enter sends chat commands; arrow keys navigate task list.
- **Screen Reader Support**: ARIA labels for icon (“Jira Task Chatbot”), sidebar (“Task Management Sidebar”), notifications (“Reminder for DOC-42”), and thumbnails (“Evidence for DOC-42”).
- **Color Contrast**: WCAG 2.1 AA compliant (e.g., 4.5:1 for blue on white). High-contrast mode uses black/white for low-vision users.
- **Focus Indicators**: Blue outlines (2px) on interactive elements.
- **Alt Text**: Evidence thumbnails include alt text (e.g., “Screenshot for DOC-42”).
- **Language**: Concise prompts (e.g., “Type a command or log in”) for cognitive accessibility.