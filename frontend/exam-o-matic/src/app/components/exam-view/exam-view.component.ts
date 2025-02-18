import { Component, Input, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface WrongAnswer {
  question: string;
  userAnswer: string[];
  correctAnswer: string[];
  options: { [key: string]: string };
}

@Component({
  selector: 'app-exam-view',
  standalone: true,
  templateUrl: './exam-view.component.html',
  styleUrls: ['./exam-view.component.css'],
  imports: [CommonModule, FormsModule],
})
export class ExamViewComponent implements OnInit {
  @Input() examName: string = '';
  @Input() practiceMode: boolean = false;  
  @Input() shuffleQuestions: boolean = true;  // Default to true for randomization
  questions: any[] = [];
  currentQuestionIndex: number = 0;
  selectedAnswers: string[] = [];
  currentAnswer: string = '';
  showResults: boolean = false;
  score: number = 0;
  wrongAnswers: WrongAnswer[] = [];
  answerSubmitted: boolean = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadQuestions();
  }

  loadQuestions() {
    this.http.get<{ questions: any[] }>(`http://127.0.0.1:8000/questions?test_bank=${this.examName}&shuffle=${this.shuffleQuestions}`)
      .subscribe(data => {
        this.questions = data.questions;
      }, error => {
        console.error("Error loading questions:", error);
      });
  }

  isMultipleChoice(): boolean {
    return this.questions.length > 0 && this.questions[this.currentQuestionIndex]?.correct_answer 
      ? this.questions[this.currentQuestionIndex].correct_answer.includes(",") 
      : false;
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
    if (!this.questions[this.currentQuestionIndex]?.correct_answer) {
      console.error("Error: correct_answer is undefined for question", this.currentQuestionIndex);
      return;
    }
  
    const correctAnswers = this.questions[this.currentQuestionIndex].correct_answer.split(',');
    const isCorrect = correctAnswers.sort().join(',') === this.selectedAnswers.sort().join(',');
  
    if (isCorrect) {
      this.score++;
    } else {
      this.wrongAnswers.push({
        question: this.questions[this.currentQuestionIndex].question,
        userAnswer: [...this.selectedAnswers],
        correctAnswer: correctAnswers,
        options: this.questions[this.currentQuestionIndex].options
      });
    }
  
    this.selectedAnswers = [];
    this.currentAnswer = '';
    this.answerSubmitted = false;
    this.currentQuestionIndex++;
  
    if (this.currentQuestionIndex >= this.questions.length) {
      this.showResults = true;
    }
  }

  getCurrentQuestionCorrectAnswers(): string[] {
    return this.questions[this.currentQuestionIndex]?.correct_answer?.split(',') || [];
  }

  isAnswerCorrect(option: string): boolean {
    return this.getCurrentQuestionCorrectAnswers().includes(option);
  }

  getAnswerLabels(answers: string[]): string {
    return answers.map(answer => `${answer}) ${this.wrongAnswers.find(wa => 
      wa.options[answer] !== undefined)?.options[answer]}`).join(', ');
  }

  restartExam() {
    window.location.reload();
  }
}
