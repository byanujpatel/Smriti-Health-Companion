export const samples = {
  care: [
    "Doctor said Papa should reduce salt from today.",
    "Papa's BP was 150 over 95 this morning.",
    "Papa ko kal raat neend nahi aayi.",
  ],
  self: [
    "I had a headache yesterday evening.",
    "I slept poorly last night.",
    "I took my vitamin D after breakfast today.",
  ],
};

export const memoryTypes = ["symptom", "medication", "vital", "visit", "document", "remark"];

export const subjects = [
  { id: "papa", name: "Papa", persona: "care" },
  { id: "mummy", name: "Mummy", persona: "care" },
  { id: "myself", name: "Myself", persona: "self" },
];
