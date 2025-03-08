import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ExamViewComponent } from './exam-view.component';

describe('ExamViewComponent', () => {
  let component: ExamViewComponent;
  let fixture: ComponentFixture<ExamViewComponent>;

  const mockQuestion = {
    id: 1,
    question: 'What is the capital of France?',
    options: {
      'A': 'London',
      'B': 'Paris',
      'C': 'Berlin',
      'D': 'Madrid'
    },
    correct_answer: 'B',
    explanation: 'Paris is the capital of France.'
  };

  const mockMultipleChoiceQuestion = {
    id: 2,
    question: 'Which of these are primary colors?',
    options: {
      'A': 'Red',
      'B': 'Green',
      'C': 'Blue',
      'D': 'Orange'
    },
    correct_answer: 'A,C',
    explanation: 'Red and Blue are primary colors.'
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExamViewComponent, HttpClientTestingModule]
    }).compileComponents();

    fixture = TestBed.createComponent(ExamViewComponent);
    component = fixture.componentInstance;
    component.practiceMode = true;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Practice Mode - Single Choice Questions', () => {
    beforeEach(() => {
      component.questions = [mockQuestion];
      component.currentQuestionIndex = 0;
      fixture.detectChanges();
    });

    it('should correctly identify right answer', () => {
      component.toggleAnswer('B');
      component.checkAnswer();
      expect(component.isCurrentAnswerCorrect()).toBeTruthy();
      expect(component.isAnswerCorrect('B')).toBeTruthy();
    });

    it('should correctly identify wrong answer', () => {
      component.toggleAnswer('A');
      component.checkAnswer();
      expect(component.isCurrentAnswerCorrect()).toBeFalsy();
      expect(component.isAnswerCorrect('A')).toBeFalsy();
    });

    it('should disable options after answer is submitted', () => {
      component.checkAnswer();
      expect(component.answerSubmitted).toBeTruthy();
    });

    it('should show explanation after answer is checked', () => {
      component.checkAnswer();
      fixture.detectChanges();
      const explanation = fixture.nativeElement.querySelector('.alert');
      expect(explanation.textContent).toContain('Paris is the capital of France');
    });
  });

  describe('Practice Mode - Multiple Choice Questions', () => {
    beforeEach(() => {
      component.questions = [mockMultipleChoiceQuestion];
      component.currentQuestionIndex = 0;
      fixture.detectChanges();
    });

    it('should handle multiple correct answers', () => {
      component.toggleAnswer('A');
      component.toggleAnswer('C');
      component.checkAnswer();
      expect(component.isCurrentAnswerCorrect()).toBeTruthy();
    });

    it('should handle partial correct answers as incorrect', () => {
      component.toggleAnswer('A');
      component.checkAnswer();
      expect(component.isCurrentAnswerCorrect()).toBeFalsy();
    });

    it('should handle incorrect combination of answers', () => {
      component.toggleAnswer('A');
      component.toggleAnswer('B');
      component.checkAnswer();
      expect(component.isCurrentAnswerCorrect()).toBeFalsy();
    });

    it('should allow toggling of multiple answers', () => {
      component.toggleAnswer('A');
      expect(component.selectedAnswers).toContain('A');
      component.toggleAnswer('C');
      expect(component.selectedAnswers).toContain('C');
      component.toggleAnswer('A');
      expect(component.selectedAnswers).not.toContain('A');
    });
  });

  describe('Question Navigation', () => {
    beforeEach(() => {
      component.questions = [mockQuestion, mockMultipleChoiceQuestion];
      component.currentQuestionIndex = 0;
      fixture.detectChanges();
    });

    it('should reset answer submitted state on next question', () => {
      component.checkAnswer();
      expect(component.answerSubmitted).toBeTruthy();
      component.nextQuestion();
      expect(component.answerSubmitted).toBeFalsy();
    });

    it('should clear selected answers on next question', () => {
      component.toggleAnswer('A');
      component.nextQuestion();
      expect(component.selectedAnswers.length).toBe(0);
    });
  });
});
