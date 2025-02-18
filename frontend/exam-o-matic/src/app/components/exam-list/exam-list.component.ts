import { Component, EventEmitter, Output } from '@angular/core';
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
  @Output() showExamList = new EventEmitter<void>();

  constructor(private http: HttpClient) {}

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
