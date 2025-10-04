// services/mathApi.ts
export interface Category {
  category_id: string;
  category_name: string;
  question_count: number;
  depth: number;
}

export interface Question {
  question_id: string;
  title: string;
  content: string;
  difficulty: string;
  category: string;
  grade: string;
  subject: string;
}

export const mathApi = {
  async getCategories(grade: string): Promise<Category[]> {
    try {
      const response = await fetch(`/api/math/categories?grade=${grade}`);
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching categories:', error);
      return [];
    }
  },

  async getQuestions(grade: string, categoryId?: string, keyword?: string): Promise<{total_count: number, questions: Question[]}> {
    try {
      const params = new URLSearchParams({ grade });
      if (categoryId) params.append('category_id', categoryId);
      if (keyword) params.append('keyword', keyword);
      
      const response = await fetch(`/api/math/questions?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch questions');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching questions:', error);
      return { total_count: 0, questions: [] };
    }
  },

  async getQuestion(questionId: string): Promise<Question | null> {
    try {
      const response = await fetch(`/api/math/question/${questionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch question');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching question:', error);
      return null;
    }
  }
};
