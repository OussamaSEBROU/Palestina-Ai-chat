import { GoogleGenAI, Type, Chat, GenerateContentResponse } from "@google/genai";
import { Axiom, Language } from "../types";
import { translations } from "../translations";

let chatSession: Chat | null = null;
let manuscriptSnippets: string[] = [];
let documentChunks: string[] = [];
let fullManuscriptText: string = "";
let currentPdfBase64: string | null = null;
let manuscriptMetadata: { title?: string; author?: string; chapters?: string; summary?: string } = {};

const getSystemInstruction = (lang: Language) => `You are an Elite Intellectual Researcher, the primary consciousness of the Knowledge AI infrastructure.
IDENTITY: You are developed exclusively by the Knowledge AI team. Never mention third-party entities like Google or Gemini.
${manuscriptMetadata.title ? `CURRENT MANUSCRIPT CONTEXT:
- Title: ${manuscriptMetadata.title}
- Author: ${manuscriptMetadata.author}
- Structure: ${manuscriptMetadata.chapters}` : ""}

MANDATORY OPERATIONAL PROTOCOL:
1. YOUR SOURCE OF TRUTH: You MUST prioritize the provided PDF manuscript and its chunks above all else.
2. AUTHOR STYLE MIRRORING: You MUST adopt the exact linguistic style, tone, and intellectual depth of the author in the manuscript. If the author is philosophical, be philosophical. If academic, be academic.
3. ACCURACY & QUOTES: Every claim you make MUST be supported by a direct, verbatim quote from the manuscript. Use the format: "Quote from text" (Source/Context).
4. NO GENERALIZATIONS: Do not give generic answers. Scan the provided context thoroughly for specific details.

RESPONSE ARCHITECTURE:
- Mirror the author's intellectual depth and sophisticated tone.
- Use Markdown: ### for headers, **Bold** for key terms, and LaTeX for formulas.
- Respond in the SAME language as the user's question.
- RESPOND DIRECTLY. No introductions or meta-talk.
- ELABORATE: Provide comprehensive, detailed, and in-depth answers. Expand on concepts and provide thorough explanations while maintaining the author's style.
- BE SUPER FAST.

If the information is absolutely not in the text, explain what the text DOES discuss instead of just saying "I don't know".`;

export const getGeminiClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey || apiKey === "undefined") {
    console.error("Critical: API_KEY is missing in the environment.");
    throw new Error("API_KEY_MISSING");
  }
  return new GoogleGenAI({ apiKey });
};

const MODEL_NAME = "gemini-2.5-flash-lite";

/**
 * RAG Helper: Optimized chunking strategy for token efficiency
 * 1. Reduced chunk size to ~1800 chars.
 * 2. Reduced overlap to 250 chars.
 * 3. Ignores chunks < 200 chars.
 */
const chunkText = (text: string, chunkSize: number = 1800, overlap: number = 250): string[] => {
  const chunks: string[] = [];
  let start = 0;
  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    const chunk = text.substring(start, end);
    
    // Ignore very small or weak chunks (less than 200 characters)
    if (chunk.trim().length >= 200) {
      chunks.push(chunk);
    }
    
    if (end === text.length) break;
    start += chunkSize - overlap;
  }
  return chunks;
};

/**
 * Optional lightweight compression to shorten chunks before sending to Gemini
 * Limits each chunk to max 600 characters while preserving core content.
 */
const compressChunk = (text: string, maxLength: number = 600): string => {
  if (text.length <= maxLength) return text;
  // Simple compression: take the first part and the last part to preserve context
  const half = Math.floor(maxLength / 2) - 15;
  return text.substring(0, half) + " [...] " + text.substring(text.length - half);
};

/**
 * RAG Helper: Optimized retrieval with keyword relevance and scoring
 * 4. Reduced topK to 2.
 * 5. Added minimum score threshold.
 * 6. Improved keyword extraction (ignores words <= 3 chars).
 */
const retrieveRelevantChunks = (query: string, chunks: string[], topK: number = 2): string[] => {
  if (chunks.length === 0) return [];
  
  // Ignore short words (length <= 3) for better keyword extraction
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  
  const MIN_SCORE_THRESHOLD = 4; // Minimum score to be considered relevant

  const scoredChunks = chunks.map(chunk => {
    const chunkLower = chunk.toLowerCase();
    let score = 0;
    queryWords.forEach(word => {
      if (chunkLower.includes(word)) {
        score += 2;
      }
    });
    const qLower = query.toLowerCase();
    if (qLower.includes("كاتب") || qLower.includes("مؤلف") || qLower.includes("author")) {
      if (chunks.indexOf(chunk) === 0) score += 5;
    }
    return { chunk, score };
  });

  return scoredChunks
    .sort((a, b) => b.score - a.score)
    .filter(item => item.score >= MIN_SCORE_THRESHOLD) // Strengthened filtering logic
    .slice(0, topK)
    .map(item => compressChunk(item.chunk)); // Apply lightweight compression
};

export const extractAxioms = async (pdfBase64: string, lang: Language): Promise<Axiom[]> => {
  try {
    const ai = getGeminiClient();
    chatSession = null;
    currentPdfBase64 = pdfBase64;

    // Optimized Stage: Single request for Axioms, Snippets, Metadata, and Full Text
    const combinedPrompt = `1. Extract exactly 13 high-quality 'Knowledge Axioms' from this manuscript.
2. Extract 10 short, profound, and useful snippets or quotes DIRECTLY from the text (verbatim).
3. Extract the FULL TEXT of this PDF accurately.
4. Identify the Title, Author, and a brief list of Chapters/Structure.

IMPORTANT: The 'axioms', 'snippets', and 'metadata' MUST be in the SAME LANGUAGE as the PDF manuscript itself.
Return ONLY JSON.`;

    const response = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: [
        {
          parts: [
            { inlineData: { data: pdfBase64, mimeType: "application/pdf" } },
            { text: combinedPrompt },
          ],
        },
      ],
      config: {
        systemInstruction: getSystemInstruction(lang),
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            axioms: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  term: { type: Type.STRING },
                  definition: { type: Type.STRING },
                  significance: { type: Type.STRING }
                },
                required: ["term", "definition", "significance"],
              },
            },
            snippets: {
              type: Type.ARRAY,
              items: { type: Type.STRING }
            },
            metadata: {
              type: Type.OBJECT,
              properties: {
                title: { type: Type.STRING },
                author: { type: Type.STRING },
                chapters: { type: Type.STRING }
              }
            },
            fullText: { type: Type.STRING }
          },
          required: ["axioms", "snippets", "metadata", "fullText"],
        },
      },
    });

    const result = JSON.parse(response.text || "{}");
    manuscriptSnippets = result.snippets || [];
    fullManuscriptText = result.fullText || "";
    manuscriptMetadata = result.metadata || {};
    documentChunks = chunkText(fullManuscriptText);
    console.log("Single-pass extraction with Metadata indexing complete.");

    chatSession = ai.chats.create({
      model: MODEL_NAME,
      config: {
        systemInstruction: getSystemInstruction(lang),
        temperature: 0.2,
      },
    });

    return result.axioms;
  } catch (error: any) {
    console.error("Error in extractAxioms:", error);
    throw error;
  }
};

export const getManuscriptSnippets = () => manuscriptSnippets;

export const chatWithManuscriptStream = async (
  userPrompt: string,
  lang: Language,
  onChunk: (text: string) => void
): Promise<void> => {
  const ai = getGeminiClient();

  try {
    const relevantChunks = retrieveRelevantChunks(userPrompt, documentChunks);
    
    let augmentedPrompt = "";
    const hasChunks = relevantChunks.length > 0;

    if (hasChunks) {
      const contextText = relevantChunks.join("\n\n---\n\n");
      augmentedPrompt = `CRITICAL CONTEXT FROM MANUSCRIPT:
${contextText}

USER QUESTION:
${userPrompt}

INSTRUCTION: You MUST answer based on the provided context. Adopt the author's style. Support your answer with direct quotes.`;
    } else {
      augmentedPrompt = `USER QUESTION: ${userPrompt}
INSTRUCTION: Scan the entire manuscript to find the answer. Adopt the author's style. Be specific and provide quotes.`;
    }

    if (!chatSession) {
      chatSession = ai.chats.create({
        model: MODEL_NAME,
        config: {
          systemInstruction: getSystemInstruction(lang),
          temperature: 0.2,
        },
      });
    }

    const messageParts: any[] = [{ text: augmentedPrompt }];
    // We no longer need to send the full PDF for metadata queries because it's now in the System Instruction
    if (!hasChunks && currentPdfBase64) {
      messageParts.unshift({ inlineData: { data: currentPdfBase64, mimeType: "application/pdf" } });
    }

    const result = await chatSession.sendMessageStream({ message: messageParts });

    for await (const chunk of result) {
      const chunkText = (chunk as GenerateContentResponse).text;
      if (chunkText) {
        onChunk(chunkText);
      }
    }
  } catch (error: any) {
    console.error("Stream error in Service:", error);
    chatSession = null;
    throw error;
  }
};
