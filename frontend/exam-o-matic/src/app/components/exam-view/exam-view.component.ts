import { Component, Input, OnInit, AfterViewInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart } from 'chart.js/auto';

interface Question {
  id: number;
  question: string;
  options: { [key: string]: string };
  correct_answer: string;
  explanation: string;
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

@Component({
  selector: 'app-exam-view',
  templateUrl: './exam-view.component.html',
  styleUrls: ['./exam-view.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class ExamViewComponent implements OnInit, AfterViewInit {
  @Input() examId: number = 0;
  @Input() examName: string = '';
  @Input() examCode: string = '';
  @Input() practiceMode: boolean = false;
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
    this.http.get<any>(`http://127.0.0.1:8000/questions?test_bank_id=${this.examId}&shuffle=${this.shuffleQuestions}`)
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
    this.http.get<any>(`http://127.0.0.1:8000/exam_history/${this.examId}`)
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
    this.answerSubmitted = true;
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
    this.http.post('http://127.0.0.1:8000/exam_results', {
      test_bank_id: this.examId,
      score: this.score,
      total_questions: this.questions.length
    }).subscribe(
      () => {
        console.log('Result saved successfully');
        this.loadExamHistory(); // Refresh history after saving
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
}