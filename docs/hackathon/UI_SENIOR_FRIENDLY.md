# Senior-Friendly UI Guide

## Design Goal

Make Smriti Saathi usable by a first-time senior citizen who may be unfamiliar with apps, uncomfortable typing, and more comfortable speaking in their own language.

The parent experience should feel like a warm check-in, not a medical form.

## Core Principles

1. One task per screen
2. Voice before typing
3. Large touch targets
4. High contrast
5. Plain language
6. No scary medical words
7. Always confirm what happened
8. Let family handle complexity

## Parent-Side UI

### Main Check-In Screen

Must show only:

- Greeting
- One large button
- Language option
- Help text

Example:

> Namaste Asha ji  
> Ready for today’s check-in?

Button:

> Start Talking

Secondary:

> I need help

### Button Rules

- Minimum 56px height
- Rounded corners
- Clear label
- Icon + text when useful
- Avoid icon-only buttons
- Keep destructive actions away from primary button

### Text Size

Recommended:

- Page title: 28-32px
- Body text: 18-20px
- Button text: 20px
- Captions: avoid when possible

### Colors

Use:

- Warm background
- Dark readable text
- High-contrast primary button
- Calm greens/blues for normal state
- Soft amber for family attention

Avoid:

- Harsh red except true errors
- Low contrast grey text
- Dense gradients behind text
- Tiny secondary links

## Parent Check-In Flow

### Screen 1: Welcome

Text:

> Namaste Asha ji. Smriti is here for your daily check-in.

Button:

> Start Check-In

### Screen 2: Listening

Text:

> I am listening. Please speak slowly.

Button:

> Stop

Visual:

- Large microphone animation or pulse
- Timer optional

### Screen 3: Confirmation

Text:

> Thank you. I saved your update for your family.

Button:

> Done

Optional:

> Add one more thing

## Check-In Conversation Copy

Use warm language:

- “How are you feeling today?”
- “Did you take your medicine?”
- “Did you eat properly?”
- “Anything you want your family to know?”

Avoid clinical language:

- “Report your symptoms”
- “Medication compliance”
- “Health incident”
- “Risk factor”

## Hindi-Friendly Copy

Use simple bilingual labels:

- Start Check-In / Check-in shuru karein
- Speak Now / Ab boliye
- Stop / Rokiye
- Saved / Save ho gaya
- Call Family / Family ko batayein

Do not overload the UI with full translations everywhere in MVP. Use the most important labels first.

## Family-Side UI

Family users can handle more detail, but the UI should still reduce anxiety.

### Dashboard Layout

Top cards:

1. Today’s check-in status
2. Latest summary
3. Family attention suggested
4. Ask Smriti

Below:

- Timeline
- Documents
- Weekly noticed changes

### Dashboard Tone

Good:

> Smriti noticed this was mentioned twice this week.

Bad:

> Abnormal health event detected.

Good:

> Family attention suggested.

Bad:

> Critical medical alert.

## Care Flag UI

### Safe Flag Labels

- Missed medicine mentioned
- Dizziness mentioned
- Pain mentioned
- Sleep trouble mentioned
- Eating less mentioned
- Check-in missed
- Document needs review

### Flag Detail Format

Each flag should show:

- What was noticed
- Date range
- Exact quote or source
- Safety line

Example:

> Dizziness mentioned twice this week.  
> Aug 1: “Subah halka chakkar tha.”  
> Aug 2: “Aaj phir chakkar laga.”  
> Smriti is not diagnosing this. Please follow up if concerned.

## Ask Smriti UI

### Suggested Questions

Show chips:

- Is Mom okay this week?
- Did she miss medicine?
- Has she mentioned dizziness before?
- What changed this week?
- What did the prescription say?

### Answer Style

Answers must include:

- Short direct answer
- Evidence dates
- Exact quotes
- No diagnosis line
- Optional next family action

## Accessibility Checklist

- [ ] Works on mobile width
- [ ] Large primary button
- [ ] Text readable without zoom
- [ ] Keyboard navigation works
- [ ] Screen reader labels on buttons
- [ ] Error messages are plain language
- [ ] No flashing animations
- [ ] Voice fallback to text exists
- [ ] Important actions confirmed
- [ ] Safety copy visible but calm

## Empty States

### No Check-Ins Yet

> No check-ins yet. Start the first one when your parent is ready.

### No Documents Yet

> Upload a prescription or report so Smriti can remember it for your family.

### No Patterns Yet

> No repeated changes noticed yet. Smriti needs a few check-ins to find patterns.

## Error States

### Voice Failed

> I could not hear clearly. Please try again or type the update.

### OCR Failed

> I could not read this document clearly. Please upload a clearer photo.

### AI Failed

> Smriti could not summarize this right now. Your original update is still saved.

## Senior-Friendly Demo Tips

- Use one parent profile
- Use Hindi greeting
- Keep check-in under 60 seconds
- Show large button clearly
- Do not show too many settings
- Let the family dashboard carry advanced AI features

## UI North Star

The parent should feel:

> This is easy. I can just talk.

The family should feel:

> I finally know what changed, with proof, without panicking.
