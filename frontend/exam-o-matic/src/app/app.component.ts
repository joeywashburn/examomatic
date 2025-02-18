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
  selectedExam: string | null = null;
  isPracticeMode = false;
  exams: {id: number, name: string, exam_code: string, notes: string}[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadExams();
  }

  loadExams() {
    this.http.get<{test_banks: TestBank[]}>('http://127.0.0.1:8000/test_banks').subscribe(
      (response) => {
        this.exams = response.test_banks.map(bank => ({
          id: bank.id,
          name: bank.name,
          exam_code: bank.exam_code || 'N/A',
          notes: bank.name === 'Default Exam' 
            ? 'This is a sample exam.' 
            : `Contains ${bank.question_count} questions`
        }));
      },
      (error) => {
        console.error('Failed to load exams:', error);
      }
    );
  }

  showExamTable() {
    this.loadExams();
    this.selectedExam = null;  
    this.showTable = true;
    this.isPracticeMode = false;
  }

  selectExam(exam: string) {
    this.selectedExam = exam;
    this.showTable = false;
    this.isPracticeMode = false;
  }

  practiceExam(exam: string) {
    this.selectedExam = exam;  
    this.showTable = false;
    this.isPracticeMode = true;
  }
}
