import os
from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"

guardrail_model = SentenceTransformer("all-MiniLM-L6-v2")

literary_semantics = [
  "analysis",
  "author",
  "austen",
  "arguments",
  "book",
  "bronte",
  "camus",
  "character",
  "character analysis",
  "chekhov",
  "criticism",
  "dante",
  "dickens",
  "dissertation",
  "dostoevsky",
  "drama",
  "essay",
  "faulkner",
  "fiction",
  "fitzgerald",
  "gogol",
  "goethe",
  "hemingway",
  "joyce",
  "kafka",
  "literary",
  "literary analysis",
  "literary criticism",
  "literary theory",
  "literature",
  "media",
  "melville",
  "morrison",
  "narrative",
  "narrative structure",
  "non-fiction",
  "novel",
  "orwell",
  "play",
  "plot",
  "plot development",
  "poem",
  "poetry",
  "prose",
  "recommend literature",
  "radio",
  "review",
  "shakespeare",
  "short story",
  "suggestion",
  "symbolism",
  "theater",
  "theory",
  "thesis",
  "tolstoy",
  "twain",
  "woolf"
]

embeddings = guardrail_model.encode(literary_semantics)
print(embeddings.shape)
class LiteraryGuardrail():
    name = "literary_guardrail"

    def get_name(self):
        return self.name

    async def run(self, agent, input, context, **kwargs):
        user_input = input.lower()

        if not any(word in user_input for word in literary_semantics):
            return {
                "status": "cancelled",
                "message": "Your question does not appear to relate to literary media. Please refine your query."
            }

        return {"status": "ok"}