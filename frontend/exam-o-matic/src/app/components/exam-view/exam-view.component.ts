import { Component, Input, OnInit, AfterViewInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart } from 'chart.js/auto';

interface Question {
  id: number;
  question: string;
  options: { [key: string]: string };
  option_images: { [key: string]: string | null };
  correct_answer: string;
  explanation: string;
  question_images: string[];
  explanation_images: string[];
}

interface WrongAnswer {
  questionNumber: number;
  question: string;
}

interface ExamResult {
  score: number;
  total_questions: number;
  timestamp: string;
  percentage: number;
}

interface AnswerResponse {
  correct: boolean;
  correct_answer: string;
  explanation: string;
  explanation_images: string[];
}

interface ImagePart {
  type: 'image';
  src: string;
}

type TextPart = string | ImagePart;

@Component({
  selector: 'app-exam-view',
  templateUrl: './exam-view.component.html',
  styleUrls: ['./exam-view.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class ExamViewComponent implements OnInit, AfterViewInit {
  @Input() examId: number | null = null;
  @Input() examName: string = '';
  @Input() examCode: string = '';
  @Input() isPracticeMode: boolean = false;
  @Input() shuffleQuestions: boolean = true;

  questions: Question[] = [];
  currentQuestionIndex: number = 0;
  selectedAnswers: string[] = [];
  currentAnswer: string = '';
  score: number = 0;
  showResults: boolean = false;
  wrongAnswers: WrongAnswer[] = [];
  loading: boolean = true;
  error: string | null = null;
  answerSubmitted: boolean = false;
  examHistory: ExamResult[] = [];
  private chart: Chart | undefined;
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';
  answerResponse: AnswerResponse | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadQuestions();
    this.loadExamHistory();
  }

  ngAfterViewInit() {
    this.updateChart();
  }

  loadQuestions() {
    this.loading = true;
    this.error = null;
    if (!this.examId) {
      this.error = 'No exam ID provided.';
      this.loading = false;
      return;
    }
    this.http.get<{ questions: Question[] }>(`${this.apiBaseUrl}/questions?test_bank_id=${this.examId}&shuffle=${this.shuffleQuestions}`)
      .subscribe(
        response => {
          console.log('API response:', response);
          this.questions = response.questions || [];
          if (this.questions.length === 0) {
            this.error = 'No questions found for this exam.';
          }
          this.loading = false;
        },
        error => {
          console.error('Error loading questions:', error);
          this.error = 'Failed to load questions. Please try again.';
          this.loading = false;
        }
      );
  }

  loadExamHistory() {
    if (!this.examId) {
      console.warn('No exam ID for history load.');
      return;
    }
    this.http.get<any>(`${this.apiBaseUrl}/exam_history/${this.examId}`)
      .subscribe(
        response => {
          this.examHistory = response.history || [];
          console.log('Exam history:', this.examHistory);
          this.updateChart();
        },
        error => {
          console.error('Error loading exam history:', error);
        }
      );
  }

  toggleAnswer(option: string) {
    if (this.isMultipleChoice()) {
      const index = this.selectedAnswers.indexOf(option);
      if (index === -1) {
        this.selectedAnswers.push(option);
      } else {
        this.selectedAnswers.splice(index, 1);
      }
    } else {
      this.currentAnswer = option;
      this.selectedAnswers = [option];
    }
  }

  checkAnswer(): void {
    const currentQuestion = this.questions[this.currentQuestionIndex];
    const answer = {
      question_id: currentQuestion.id,
      selected_answer: this.isMultipleChoice() ? this.selectedAnswers.join(',') : this.currentAnswer
    };

    this.http.post<AnswerResponse>(`${this.apiBaseUrl}/answer`, answer)
      .subscribe({
        next: (response) => {
          this.answerResponse = response;
          this.answerSubmitted = true;
        },
        error: (error) => {
          console.error('Error checking answer:', error);
        }
      });
  }

  nextQuestion(): void {
    if (!this.questions[this.currentQuestionIndex].correct_answer) {
      console.error("Error: correct_answer is undefined for question", this.currentQuestionIndex);
      return;
    }
  
    const correctAnswers = this.questions[this.currentQuestionIndex].correct_answer.split(',');
    const userAnswers = this.isMultipleChoice() ? this.selectedAnswers : [this.currentAnswer];
    const isCorrect = correctAnswers.sort().join(',') === userAnswers.sort().join(',');
  
    if (isCorrect) {
      this.score++;
    } else {
      this.wrongAnswers.push({
        questionNumber: this.currentQuestionIndex + 1,
        question: this.questions[this.currentQuestionIndex].question
      });
    }
  
    this.selectedAnswers = [];
    this.currentAnswer = '';
    this.answerSubmitted = false;
    this.answerResponse = null;
  
    if (this.currentQuestionIndex < this.questions.length - 1) {
      this.currentQuestionIndex++;
    } else {
      this.showResults = true;
      this.saveResult();
    }
  }

  isMultipleChoice(): boolean {
    return this.questions[this.currentQuestionIndex].correct_answer.includes(',');
  }

  getAvailableOptions(): string[] {
    const options = this.questions[this.currentQuestionIndex]?.options;
    if (!options || typeof options !== 'object') {
      console.error('No valid options for question', this.currentQuestionIndex, options);
      return [];
    }
    return Object.keys(options).sort();
  }

  getCurrentQuestionCorrectAnswers(): string[] {
    return this.questions[this.currentQuestionIndex].correct_answer.split(',') || [];
  }

  isCurrentAnswerCorrect(): boolean {
    const correctAnswers = this.getCurrentQuestionCorrectAnswers();
    const userAnswers = this.isMultipleChoice() ? this.selectedAnswers : [this.currentAnswer];
    return correctAnswers.sort().join(',') === userAnswers.sort().join(',');
  }

  isAnswerCorrect(option: string): boolean {
    return this.getCurrentQuestionCorrectAnswers().includes(option);
  }

  saveResult() {
    if (!this.examId) {
      console.error('Cannot save result: examId is null');
      return;
    }
    this.http.post(`${this.apiBaseUrl}/exam_results`, {
      test_bank_id: this.examId,
      score: this.score,
      total_questions: this.questions.length
    }).subscribe(
      () => {
        console.log('Result saved successfully');
        this.loadExamHistory();
      },
      error => console.error('Error saving result:', error)
    );
  }

  restartExam() {
    window.location.reload();
  }

  updateChart() {
    if (this.chart) {
      this.chart.destroy();
    }
    const ctx = document.getElementById('scoreChart') as HTMLCanvasElement;
    if (ctx && this.examHistory.length > 0) {
      this.chart = new Chart(ctx, {
        type: 'line',
        data: this.getChartData(),
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              title: { display: true, text: 'Percentage (%)' }
            },
            x: {
              title: { display: true, text: 'Date' }
            }
          }
        }
      });
    }
  }

  getChartData() {
    const labels = this.examHistory.map(r => new Date(r.timestamp).toLocaleDateString());
    const data = this.examHistory.map(r => r.percentage);
    return {
      labels: labels,
      datasets: [{
        label: 'Score Percentage (%)',
        data: data,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }]
    };
  }

  // Type guard method to check if a TextPart is an ImagePart
  isImagePart(part: TextPart): part is ImagePart {
    return typeof part !== 'string' && 'type' in part && part.type === 'image';
  }

  parseTextWithImages(text: string, images: string[]): TextPart[] {
    const parts: TextPart[] = [];
    let remainingText = text;

    const placeholderRegex = /\[image(\d+)\]/g;
    let match;
    let lastIndex = 0;

    while ((match = placeholderRegex.exec(text)) !== null) {
      const placeholder = match[0]; // e.g., [image1]
      const imageIndex = parseInt(match[1], 10) - 1; // e.g., 0 for image1
      const imageSrc = images[imageIndex];

      if (match.index > lastIndex) {
        parts.push(remainingText.substring(lastIndex, match.index));
      }

      if (imageSrc) {
        parts.push({ type: 'image', src: imageSrc });
      }

      lastIndex = match.index + placeholder.length;
    }

    if (lastIndex < remainingText.length) {
      parts.push(remainingText.substring(lastIndex));
    }

    return parts;
  }

  parseExplanationText(text: string, images: string[]): TextPart[] {
    const parts: TextPart[] = [];
    let remainingText = text;

    const placeholderRegex = /\[explanation_image(\d+)\]/g;
    let match;
    let lastIndex = 0;

    while ((match = placeholderRegex.exec(text)) !== null) {
      const placeholder = match[0]; // e.g., [explanation_image1]
      let imageIndex: number;
      try {
        imageIndex = parseInt(match[1], 10) - 1; // e.g., 0 for explanation_image1
      } catch (e) {
        console.error(`Invalid image index in placeholder ${placeholder}: ${e}`);
        continue;
      }
      const imageSrc = images[imageIndex];

      if (match.index > lastIndex) {
        parts.push(remainingText.substring(lastIndex, match.index));
      }

      if (imageSrc) {
        parts.push({ type: 'image', src: imageSrc });
      } else {
        console.warn(`No image found for placeholder ${placeholder} at index ${imageIndex}`);
      }

      lastIndex = match.index + placeholder.length;
    }

    if (lastIndex < remainingText.length) {
      parts.push(remainingText.substring(lastIndex));
    }

    return parts;
  }
}