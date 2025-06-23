// src/app/app.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { ExamListComponent } from './components/exam-list/exam-list.component';
import { ExamViewComponent } from './components/exam-view/exam-view.component';

interface TestBank {
  id: number;
  name: string;
  exam_code: string;
  question_count: number;
  last_three_scores: (number | null)[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [CommonModule, HttpClientModule, ExamListComponent, ExamViewComponent],
})
export class AppComponent implements OnInit {
  showTable = true;
  selectedExamId: number | null = null;
  isPracticeMode = false;
  exams: { id: number; name: string; exam_code: string; notes: string; last_score: number | null }[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadExams();
  }

  loadExams() {
    this.http.get<{ test_banks: TestBank[] }>('http://127.0.0.1:8000/test_banks').subscribe(
      (response) => {
        this.exams = response.test_banks.map(bank => ({
          id: bank.id,
          name: bank.name,
          exam_code: bank.exam_code || 'N/A',
          notes: bank.name === 'Default Exam'
            ? 'This is a sample exam.'
            : `Contains ${bank.question_count} questions`,
          last_score: bank.last_three_scores[0] // Map the first score from last_three_scores
        }));
      },
      (error) => {
        console.error('Failed to load exams:', error);
      }
    );
  }

  getSelectedExamName(): string {
    if (!this.selectedExamId) return '';
    const exam = this.exams.find(e => e.id === this.selectedExamId);
    return exam?.name || '';
  }

  getSelectedExamCode(): string {
    if (!this.selectedExamId) return '';
    const exam = this.exams.find(e => e.id === this.selectedExamId);
    return exam?.exam_code || '';
  }

  showExamTable() {
    this.loadExams();
    this.selectedExamId = null;
    this.showTable = true;
    this.isPracticeMode = false;
  }

  selectExam(examId: number) {
    this.selectedExamId = examId;
    this.showTable = false;
    this.isPracticeMode = false;
  }

  practiceExam(examId: number) {
    this.selectedExamId = examId;
    this.showTable = false;
    this.isPracticeMode = true;
  }

  deleteExam(examId: number) {
    if (confirm('Are you sure you want to delete this exam? This action cannot be undone.')) {
      this.http.delete(`http://127.0.0.1:8000/test_banks/${examId}`).subscribe(
        () => {
          this.loadExams();
          if (this.selectedExamId === examId) {
            this.selectedExamId = null;
          }
        },
        (error) => {
          console.error('Failed to delete exam:', error);
          alert('Failed to delete exam. Please try again.');
        }
      );
    }
  }
}