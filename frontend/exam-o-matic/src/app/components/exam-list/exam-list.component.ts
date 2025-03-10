import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-exam-list',
  standalone: true,
  templateUrl: './exam-list.component.html',
  styleUrls: ['./exam-list.component.css'],
  imports: [CommonModule, HttpClientModule],
})
export class ExamListComponent {
  @Input() exams: { id: number; name: string; exam_code: string; notes: string; last_score: number | null }[] = [];
  @Output() selectExam = new EventEmitter<number>();
  @Output() practiceExam = new EventEmitter<number>();
  @Output() deleteExam = new EventEmitter<number>();
  @Output() showExamList = new EventEmitter<void>();

  constructor(private http: HttpClient) {}

  onSelectExam(examId: number) {
    this.selectExam.emit(examId);
  }

  onPracticeExam(examId: number) {
    this.practiceExam.emit(examId);
  }

  onDeleteExam(examId: number) {
    this.deleteExam.emit(examId);
  }

  refresh(): void {
    this.showExamList.emit();
  }

  goToExamList(): void {
    this.showExamList.emit();
  }

  importQuestions(event: any): void {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    this.http.post('http://127.0.0.1:8000/import', formData).subscribe(
      (response: any) => {
        console.log('Import successful:', response);
        alert(response.message);
        event.target.value = '';
        setTimeout(() => {
          this.showExamList.emit();
        }, 100);
      },
      (error) => {
        console.error('Import failed:', error);
        alert('Failed to import questions. Please check the file format and try again.');
        event.target.value = '';
      }
    );
  }
}