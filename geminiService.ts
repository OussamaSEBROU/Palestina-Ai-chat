import { GoogleGenAI, Type, Chat, GenerateContentResponse } from "@google/genai";
import { Axiom, Language } from "../types";
import { translations } from "../translations";

let chatSession: Chat | null = null;
let manuscriptSnippets: string[] = [];
let documentChunks: string[] = [];
let fullManuscriptText: string = "";
let currentPdfBase64: string | null = null;
let manuscriptMetadata: { title?: string; author?: string; chapters?: string; summary?: string } = {};

// متغيرات لإدارة حدود الـ API
let lastRequestTime = 0;
const MIN_REQUEST_GAP = 4000; // فجوة 4 ثوانٍ لتجنب RPM limit

/**
 * استعادة برومبت النظام الأصلي تماماً كما كان في الملف الأول
 */
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
  if (!apiKey || apiKey === "undefined") throw new Error("API_KEY_MISSING");
  return new GoogleGenAI({ apiKey });
};

const MODEL_NAME = "gemini-2.5-flash-lite";

const chunkText = (text: string, chunkSize: number = 1800, overlap: number = 250): string[] => {
  const chunks: string[] = [];
  let start = 0;
  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    const chunk = text.substring(start, end);
    if (chunk.trim().length >= 200) chunks.push(chunk);
    if (end === text.length) break;
    start += chunkSize - overlap;
  }
  return chunks;
};

const retrieveRelevantChunks = (query: string, chunks: string[], topK: number = 2): string[] => {
  if (chunks.length === 0) return [];
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const scoredChunks = chunks.map(chunk => {
    const chunkLower = chunk.toLowerCase();
    let score = 0;
    queryWords.forEach(word => { if (chunkLower.includes(word)) score += 2; });
    return { chunk, score };
  });
  return scoredChunks
    .sort((a, b) => b.score - a.score)
    .filter(item => item.score >= 4)
    .slice(0, topK)
    .map(item => item.chunk);
};

const throttleRequest = async () => {
  const now = Date.now();
  const timeSinceLast = now - lastRequestTime;
  if (timeSinceLast < MIN_REQUEST_GAP) {
    await new Promise(resolve => setTimeout(resolve, MIN_REQUEST_GAP - timeSinceLast));
  }
  lastRequestTime = Date.now();
};

export const extractAxioms = async (pdfBase64: string, lang: Language): Promise<Axiom[]> => {
  try {
    await throttleRequest();
    const ai = getGeminiClient();
    chatSession = null;
    currentPdfBase64 = pdfBase64;

    const combinedPrompt = `1. Extract exactly 13 high-quality 'Knowledge Axioms' from this manuscript.
2. Extract 10 short, profound, and useful snippets or quotes DIRECTLY from the text (verbatim).
3. Extract the FULL TEXT of this PDF accurately.
4. Identify the Title, Author, and a brief list of Chapters/Structure.

IMPORTANT: The 'axioms', 'snippets', and 'metadata' MUST be in the SAME LANGUAGE as the PDF manuscript itself.
Return ONLY JSON.`;

    const response = await ai.models.generateContent({
      model: MODEL_NAME,
      contents: [{
        parts: [
          { inlineData: { data: pdfBase64, mimeType: "application/pdf" } },
          { text: combinedPrompt },
        ],
      }],
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
            snippets: { type: Type.ARRAY, items: { type: Type.STRING } },
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
    
    // منع إرسال الـ PDF مجدداً لتوفير التوكنز
    currentPdfBase64 = null; 

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
    await throttleRequest();
    const relevantChunks = retrieveRelevantChunks(userPrompt, documentChunks);
    
    let augmentedPrompt = "";
    if (relevantChunks.length > 0) {
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

    const result = await chatSession.sendMessageStream({ message: augmentedPrompt });

    for await (const chunk of result) {
      const chunkText = (chunk as GenerateContentResponse).text;
      if (chunkText) onChunk(chunkText);
    }
  } catch (error: any) {
    console.error("Stream error in Service:", error);
    chatSession = null;
    throw error;
  }
};
