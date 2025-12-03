import { GoogleGenerativeAI } from "@google/generative-ai";

export class GeminiScoringService {
    private genAI: GoogleGenerativeAI;
    private model: any;

    constructor(apiKey: string) {
        this.genAI = new GoogleGenerativeAI(apiKey);
        // User requested latest Gemini (2.0 Flash Experimental)
        this.model = this.genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });
    }

    async analyzeScene(text: string, context: string = ""): Promise<any> {
        try {
            const prompt = `
        Analyze the following video scene text/transcript for marketing effectiveness.
        
        SCENE TEXT: "${text}"
        CONTEXT: ${context}
        
        Evaluate and return a JSON object with:
        1. "pain_point_score" (0-10): Intensity of the problem/pain described.
        2. "hook_score" (0-10): How attention-grabbing is it?
        3. "demographic_appeal": List of likely demographics (e.g., "Male 20-30", "Fitness Enthusiasts").
        4. "reasoning": Brief explanation of the scores.
        
        JSON OUTPUT ONLY.
      `;

            const result = await this.model.generateContent(prompt);
            const response = await result.response;
            const textResponse = response.text();

            // Clean up markdown code blocks if present
            const jsonStr = textResponse.replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonStr);
        } catch (error) {
            console.error("Gemini Analysis Failed:", error);
            // Fallback to "dumb" values if AI fails, but log it
            return {
                pain_point_score: 5,
                hook_score: 5,
                demographic_appeal: ["Unknown"],
                reasoning: "AI Analysis Failed"
            };
        }
    }
}
