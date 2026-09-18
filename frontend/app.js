document.addEventListener('DOMContentLoaded', () => {
  const stageSteps = document.querySelectorAll('.stage-step');
  const stageSections = document.querySelectorAll('.stage-card');
  const errorBanner = document.getElementById('error-banner');
  const studentStatusLine = document.getElementById('student-status-line');
  const resetSessionBtn = document.getElementById('reset-session-btn');

  // Stage 1: Goal
  const goalForm = document.getElementById('goal-form');
  const goalInput = document.getElementById('goal-input');
  const daysInput = document.getElementById('days-input');
  const levelSelect = document.getElementById('level-select');
  const startLearningBtn = document.getElementById('start-learning-btn');

  // Stage 2: Assessment
  const diagnosticQuestionsContainer = document.getElementById('diagnostic-questions-container');
  const submitAssessmentBtn = document.getElementById('submit-assessment-btn');
  const assessmentResultBox = document.getElementById('assessment-result-box');
  const assessedLevelDisplay = document.getElementById('assessed-level-display');
  const assessmentSummaryText = document.getElementById('assessment-summary-text');
  const continueToPlanBtn = document.getElementById('continue-to-plan-btn');

  // Stage 3: Plan
  const planRoadmapTitle = document.getElementById('plan-roadmap-title');
  const roadmapList = document.getElementById('roadmap-list');
  const startFirstLessonBtn = document.getElementById('start-first-lesson-btn');

  // Stage 4: Learn / Concept
  const learnTopicTitle = document.getElementById('learn-topic-title');
  const learnExplanation = document.getElementById('learn-explanation');
  const learnKeyPoints = document.getElementById('learn-key-points');
  const learnSourcesTags = document.getElementById('learn-sources-tags');
  const goToQuizBtn = document.getElementById('go-to-quiz-btn');

  // Stage 5: Quiz
  const quizTopicTitle = document.getElementById('quiz-topic-title');
  const quizQuestionsForm = document.getElementById('quiz-questions-form');
  const submitQuizBtn = document.getElementById('submit-quiz-btn');
  const quizResultCard = document.getElementById('quiz-result-card');
  const quizScoreFraction = document.getElementById('quiz-score-fraction');
  const quizScorePct = document.getElementById('quiz-score-pct');
  const quizStatusTitle = document.getElementById('quiz-status-title');
  const quizScoreFeedback = document.getElementById('quiz-score-feedback');
  const quizBreakdownList = document.getElementById('quiz-breakdown-list');
  const continueToPracticeBtn = document.getElementById('continue-to-practice-btn');

  // Stage 6: Practice
  const practiceExerciseTitle = document.getElementById('practice-exercise-title');
  const practiceProblemStatement = document.getElementById('practice-problem-statement');
  const practiceExpectedContainer = document.getElementById('practice-expected-container');
  const practiceExpectedOutput = document.getElementById('practice-expected-output');
  const practiceCodeArea = document.getElementById('practice-code-area');
  const practiceHintsList = document.getElementById('practice-hints-list');
  const resetCodeBtn = document.getElementById('reset-code-btn');
  const runCodeBtn = document.getElementById('run-code-btn');
  const practiceConsoleContainer = document.getElementById('practice-console-container');
  const consoleStatusIndicator = document.getElementById('console-status-indicator');
  const practiceConsoleOutput = document.getElementById('practice-console-output');
  const clearConsoleBtn = document.getElementById('clear-console-btn');
  const submitPracticeBtn = document.getElementById('submit-practice-btn');

  // Stage 7: Performance & Conditional Routing
  const perfQuizScore = document.getElementById('perf-quiz-score');
  const perfPracticeScore = document.getElementById('perf-practice-score');
  const perfOverallScore = document.getElementById('perf-overall-score');
  const perfPaceStatus = document.getElementById('perf-pace-status');
  const perfStrongList = document.getElementById('perf-strong-list');
  const perfWeakList = document.getElementById('perf-weak-list');
  const evaluatorFeedbackText = document.getElementById('evaluator-feedback-text');
  const routingDecisionPill = document.getElementById('routing-decision-pill');
  const routingDecisionText = document.getElementById('routing-decision-text');
  const plannerUpdateBox = document.getElementById('planner-update-box');
  const plannerUpdateText = document.getElementById('planner-update-text');
  const nextTaskBtn = document.getElementById('next-task-btn');
  const nextTaskBtnText = document.getElementById('next-task-btn-text');
  const workflowStepsFlow = document.getElementById('workflow-steps-flow');

  // Persistent Drawer
  const drawerToggle = document.getElementById('drawer-toggle');
  const drawerContent = document.getElementById('drawer-content');
  const masteryBadges = document.getElementById('mastery-badges');
  const sessionsHistoryList = document.getElementById('sessions-history-list');

  const currentStudentId = 'student_default';
  let activeStudyData = null;
  let starterPracticeCodeBackup = '';

  const defaultDiagnostics = [
    {
      id: 1,
      question: 'What is a Python function?',
      options: [
        'A) A reusable block of code designed to perform a specific task',
        'B) A database management system',
        'C) A variable that stores numbers only',
        'D) An operating system program'
      ],
      correct_option: 'A'
    },
    {
      id: 2,
      question: 'Which keyword is used in Python to define a function?',
      options: ['A) func', 'B) def', 'C) function', 'D) lambda_func'],
      correct_option: 'B'
    },
    {
      id: 3,
      question: 'What is the average time complexity of looking up a key in a Python dictionary?',
      options: ['A) O(n)', 'B) O(log n)', 'C) O(1)', 'D) O(n^2)'],
      correct_option: 'C'
    }
  ];

  initApp();

  function initApp() {
    loadProgressAndHistory();
    setupStageNav();
    showStage('stage-goal');
  }

  function showStage(stageId) {
    stageSections.forEach(sec => {
      sec.classList.add('hidden');
    });
    const target = document.getElementById(stageId);
    if (target) {
      target.classList.remove('hidden');
    }

    let reachedActive = false;
    stageSteps.forEach(step => {
      const stepStage = step.getAttribute('data-stage');
      if (stepStage === stageId) {
        step.classList.add('active');
        step.classList.remove('completed');
        reachedActive = true;
      } else if (!reachedActive) {
        step.classList.remove('active');
        step.classList.add('completed');
      } else {
        step.classList.remove('active');
        step.classList.remove('completed');
      }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function setupStageNav() {
    stageSteps.forEach(step => {
      step.addEventListener('click', () => {
        const stageId = step.getAttribute('data-stage');
        if (activeStudyData || stageId === 'stage-goal') {
          showStage(stageId);
        }
      });
    });

    drawerToggle.addEventListener('click', () => {
      drawerContent.classList.toggle('hidden');
      const icon = drawerToggle.querySelector('.drawer-icon');
      icon.textContent = drawerContent.classList.contains('hidden') ? '▶' : '▼';
    });

    if (resetSessionBtn) {
      resetSessionBtn.addEventListener('click', (e) => {
        e.preventDefault();
        resetToNewGoal();
      });
    }
  }

  function resetToNewGoal() {
    activeStudyData = null;
    starterPracticeCodeBackup = '';
    hideError();

    // Reset Goal Form fields
    if (goalInput) {
      goalInput.value = '';
      goalInput.placeholder = 'e.g. I want to learn Python for backend development in 30 days';
    }
    if (daysInput) daysInput.value = '30';
    if (levelSelect) levelSelect.value = 'beginner';
    setLoading(startLearningBtn, false, 'Start Learning');

    // Reset Stage 2: Assessment
    if (diagnosticQuestionsContainer) diagnosticQuestionsContainer.innerHTML = '';
    if (assessmentResultBox) assessmentResultBox.classList.add('hidden');
    if (submitAssessmentBtn) {
      submitAssessmentBtn.classList.remove('hidden');
      setLoading(submitAssessmentBtn, false, 'Submit Assessment');
    }

    // Reset Stage 3: Learning Plan
    if (roadmapList) roadmapList.innerHTML = '';
    if (planRoadmapTitle) planRoadmapTitle.textContent = 'Your Learning Roadmap';
    if (startFirstLessonBtn) setLoading(startFirstLessonBtn, false, 'Start Current Lesson →');

    // Reset Stage 4: Learn / Concept
    if (learnTopicTitle) learnTopicTitle.textContent = 'Current Topic: Python Fundamentals & Data Structures';
    if (learnExplanation) learnExplanation.innerHTML = '';
    if (learnKeyPoints) learnKeyPoints.innerHTML = '';
    if (learnSourcesTags) learnSourcesTags.innerHTML = '';

    // Reset Stage 5: Quiz
    if (quizQuestionsForm) quizQuestionsForm.innerHTML = '';
    if (quizResultCard) quizResultCard.classList.add('hidden');
    const quizActions = document.getElementById('quiz-actions-container');
    if (quizActions) quizActions.classList.remove('hidden');
    if (submitQuizBtn) setLoading(submitQuizBtn, false, 'Submit Quiz');

    // Reset Stage 6: Practice
    if (practiceProblemStatement) practiceProblemStatement.textContent = '';
    if (practiceExpectedOutput) practiceExpectedOutput.textContent = '';
    if (practiceHintsList) practiceHintsList.innerHTML = '';
    if (practiceCodeArea) practiceCodeArea.value = '';
    if (practiceConsoleContainer) practiceConsoleContainer.classList.add('hidden');
    if (practiceConsoleOutput) practiceConsoleOutput.textContent = '';
    if (submitPracticeBtn) setLoading(submitPracticeBtn, false, 'Submit Solution for Evaluation →');
    if (runCodeBtn) setLoading(runCodeBtn, false, '▶ Run Code');

    // Reset Stage 7: Performance & Conditional Routing
    if (perfStrongList) perfStrongList.innerHTML = '';
    if (perfWeakList) perfWeakList.innerHTML = '';
    if (evaluatorFeedbackText) evaluatorFeedbackText.textContent = '';
    if (routingDecisionText) routingDecisionText.textContent = '';
    if (plannerUpdateBox) plannerUpdateBox.classList.add('hidden');
    if (workflowStepsFlow) workflowStepsFlow.innerHTML = '';
    if (nextTaskBtn) setLoading(nextTaskBtn, false, 'Proceed to Next Task →');

    // Show Stage 1 & smooth scroll to top
    showStage('stage-goal');

    // Focus input so user can type new goal immediately
    if (goalInput) {
      goalInput.focus();
    }
  }

  // STAGE 1: GOAL
  goalForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const goal = goalInput.value.trim();
    const days = parseInt(daysInput.value, 10) || 30;
    const selectedLevel = levelSelect.value;
    if (!goal) return;

    hideError();
    activeStudyData = {
      student_id: currentStudentId,
      learning_goal: goal,
      target_days: days,
      assessed_level: selectedLevel,
      current_day: 1
    };

    renderAssessmentStage(activeStudyData);
    showStage('stage-assessment');
  });

  // STAGE 2: ASSESSMENT
  function renderAssessmentStage(data) {
    const questions = (data.assessment && data.assessment.questions && data.assessment.questions.length > 0)
      ? data.assessment.questions
      : defaultDiagnostics;

    diagnosticQuestionsContainer.innerHTML = '';
    questions.forEach((q, idx) => {
      const qDiv = document.createElement('div');
      qDiv.className = 'question-block';
      let optionsHtml = '';
      q.options.forEach((opt, oIdx) => {
        const letter = String.fromCharCode(65 + oIdx);
        optionsHtml += '<label class="option-label"><input type="radio" name="diag-q-' + q.id + '" value="' + letter + '" /> <span>' + escapeHtml(opt) + '</span></label>';
      });

      qDiv.innerHTML = '<div class="question-title">Question ' + (idx + 1) + ' of ' + questions.length + ': ' + escapeHtml(q.question) + '</div><div class="options-group">' + optionsHtml + '</div>';
      diagnosticQuestionsContainer.appendChild(qDiv);
    });

    assessmentResultBox.classList.add('hidden');
    submitAssessmentBtn.classList.remove('hidden');
  }

  submitAssessmentBtn.addEventListener('click', async () => {
    hideError();

    const answers = {};
    const questionBlocks = diagnosticQuestionsContainer.querySelectorAll('.question-block');
    let hasUnanswered = false;

    questionBlocks.forEach((_, idx) => {
      const qid = idx + 1;
      const selected = document.querySelector('input[name="diag-q-' + qid + '"]:checked');
      if (!selected) {
        hasUnanswered = true;
      } else {
        answers[qid] = selected.value;
      }
    });

    if (hasUnanswered) {
      showError('Please select an answer for all 3 diagnostic questions before submitting.');
      return;
    }

    setLoading(submitAssessmentBtn, true, 'Evaluating Assessment & Building Roadmap...');

    const goal = (activeStudyData && activeStudyData.learning_goal) || goalInput.value.trim() || 'Python for backend development in 30 days';
    const days = (activeStudyData && activeStudyData.target_days) || parseInt(daysInput.value, 10) || 30;
    const assessedLevel = (activeStudyData && activeStudyData.assessed_level) || levelSelect.value || 'beginner';

    try {
      const res = await fetch('/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: currentStudentId,
          learning_goal: goal,
          target_days: days,
          assessed_level: assessedLevel,
          quiz_answers: answers,
          action: 'assess_submit'
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error evaluating assessment.');

      activeStudyData = data;
      renderAssessmentResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(submitAssessmentBtn, false, 'Submit Assessment');
    }
  });

  function renderAssessmentResult(data) {
    const level = (data.assessed_level || 'beginner').toUpperCase();
    assessedLevelDisplay.textContent = level;
    assessmentSummaryText.textContent = data.assessment?.diagnostic_summary || ('Assessed at ' + level + ' level. Customized learning roadmap generated.');

    submitAssessmentBtn.classList.add('hidden');
    assessmentResultBox.classList.remove('hidden');
    loadProgressAndHistory();
  }

  continueToPlanBtn.addEventListener('click', () => {
    renderPlanStage(activeStudyData);
    showStage('stage-plan');
  });

  // STAGE 3: PLAN
  function renderPlanStage(data) {
    planRoadmapTitle.textContent = 'Roadmap for ' + (data.learning_goal || 'Python Backend');
    roadmapList.innerHTML = '';

    const items = data.roadmap || [];
    items.forEach((item, idx) => {
      const card = document.createElement('div');
      card.className = 'roadmap-card ' + (item.status || 'pending');
      
      let statusBadge = '⏳ Pending';
      if (item.status === 'in_progress') statusBadge = '→ Current Focus';
      if (item.status === 'mastered') statusBadge = '✓ Mastered';
      if (item.status === 'reinforcing') statusBadge = '⚠️ Reinforcing';

      card.innerHTML = '<div class="topic-meta"><span class="badge ' + (item.status === 'mastered' ? 'badge-success' : 'badge-primary') + '">Day ' + (item.target_day || (idx + 1) * 5) + '</span><h4>' + escapeHtml(item.topic) + '</h4><p>' + escapeHtml(item.description || 'Core concepts, architecture, and practical coding.') + '</p></div><span class="status-indicator">' + statusBadge + '</span>';
      roadmapList.appendChild(card);
    });

    studentStatusLine.textContent = 'Day ' + (data.current_day || 1) + ' of ' + (data.target_days || 30) + ' • Topic: ' + data.current_topic;
  }

  startFirstLessonBtn.addEventListener('click', () => {
    renderLearnStage(activeStudyData);
    showStage('stage-learn');
  });

  // STAGE 4: LEARN
  function renderLearnStage(data) {
    const teaching = data.teaching || {};
    learnTopicTitle.textContent = 'Current Topic: ' + (data.current_topic || 'Python Fundamentals');
    learnExplanation.innerHTML = '<p>' + escapeHtml(teaching.explanation || 'Loading comprehensive concept explanation...') + '</p>';

    learnKeyPoints.innerHTML = '';
    (teaching.key_points || [
      'Master underlying language semantics and data structures',
      'Understand space and time complexity tradeoffs',
      'Write modular, testable backend application logic'
    ]).forEach(pt => {
      const li = document.createElement('li');
      li.textContent = pt;
      learnKeyPoints.appendChild(li);
    });

    learnSourcesTags.innerHTML = '';
    (teaching.grounded_sources || ['Python Backend Reference', 'Data Structures & Memory Models']).forEach(src => {
      const tag = document.createElement('span');
      tag.className = 'grounding-tag';
      tag.textContent = '📖 ' + src;
      learnSourcesTags.appendChild(tag);
    });
  }

  goToQuizBtn.addEventListener('click', () => {
    renderQuizStage(activeStudyData);
    showStage('stage-quiz');
  });

  // STAGE 5: QUIZ
  function renderQuizStage(data) {
    quizTopicTitle.textContent = 'Knowledge Check: ' + data.current_topic;
    quizQuestionsForm.innerHTML = '';
    quizResultCard.classList.add('hidden');
    document.getElementById('quiz-actions-container').classList.remove('hidden');

    let questions = [];
    if (data.quiz_multi && data.quiz_multi.questions && data.quiz_multi.questions.length > 0) {
      questions = data.quiz_multi.questions;
    } else if (data.quiz) {
      questions = [data.quiz];
    } else {
      questions = [
        {
          id: 1,
          question: 'What does a Python function allow you to do?',
          options: ['A) Store data permanently', 'B) Reuse a block of code', 'C) Create a database', 'D) Install Python'],
          correct_option: 'B'
        },
        {
          id: 2,
          question: 'Which keyword defines a function?',
          options: ['A) class', 'B) def', 'C) function', 'D) func'],
          correct_option: 'B'
        },
        {
          id: 3,
          question: 'What is returned by default if no return statement is present?',
          options: ['A) None', 'B) 0', 'C) False', 'D) Empty string'],
          correct_option: 'A'
        }
      ];
    }

    questions.forEach((q, idx) => {
      const qDiv = document.createElement('div');
      qDiv.className = 'question-block';
      let optionsHtml = '';
      q.options.forEach((opt, oIdx) => {
        const letter = String.fromCharCode(65 + oIdx);
        optionsHtml += '<label class="option-label"><input type="radio" name="quiz-q-' + q.id + '" value="' + letter + '" /> <span>' + escapeHtml(opt) + '</span></label>';
      });

      qDiv.innerHTML = '<div class="question-title">Question ' + (idx + 1) + ' of ' + questions.length + ': ' + escapeHtml(q.question) + '</div><div class="options-group">' + optionsHtml + '</div>';
      quizQuestionsForm.appendChild(qDiv);
    });
  }

  submitQuizBtn.addEventListener('click', async () => {
    hideError();

    const answers = {};
    const questionBlocks = quizQuestionsForm.querySelectorAll('.question-block');
    let hasUnanswered = false;

    questionBlocks.forEach((_, idx) => {
      const qid = idx + 1;
      const selected = document.querySelector('input[name="quiz-q-' + qid + '"]:checked');
      if (!selected) {
        hasUnanswered = true;
      } else {
        answers[qid] = selected.value;
      }
    });

    if (hasUnanswered) {
      showError('Please select an answer for all quiz questions before submitting.');
      return;
    }

    setLoading(submitQuizBtn, true, 'Evaluating Quiz...');

    try {
      const res = await fetch('/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: currentStudentId,
          learning_goal: activeStudyData.learning_goal,
          quiz_answers: answers,
          quiz_answer: answers[1] || 'A',
          action: 'quiz_submit'
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error grading quiz.');

      activeStudyData = data;
      renderQuizResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(submitQuizBtn, false, 'Submit Quiz');
    }
  });

  function renderQuizResult(data) {
    const qResult = data.quiz_result || {
      score: 4,
      total: 5,
      percentage: 80,
      question_results: [],
      areas_to_improve: []
    };

    quizScoreFraction.textContent = qResult.score + ' / ' + qResult.total;
    quizScorePct.textContent = qResult.percentage + '%';
    quizStatusTitle.textContent = qResult.percentage >= 70 ? 'Quiz Passed 🎉' : 'Quiz Needs Review ⚠️';
    quizScoreFeedback.textContent = qResult.percentage >= 70
      ? 'Solid understanding of foundational concepts.'
      : 'Some key questions were missed. Review the explanations below.';

    quizBreakdownList.innerHTML = '';
    (qResult.question_results || []).forEach(r => {
      const item = document.createElement('div');
      item.className = 'breakdown-item ' + (r.is_correct ? 'breakdown-correct' : 'breakdown-incorrect');
      item.innerHTML = '<span>' + (r.is_correct ? '✓' : '✗') + '</span><div><strong>' + escapeHtml(r.question) + '</strong><div>Your Answer: ' + r.student_answer + ' | Correct: ' + r.correct_option + '</div><small>' + escapeHtml(r.explanation) + '</small></div>';
      quizBreakdownList.appendChild(item);
    });

    document.getElementById('quiz-actions-container').classList.add('hidden');
    quizResultCard.classList.remove('hidden');
  }

  continueToPracticeBtn.addEventListener('click', () => {
    renderPracticeStage(activeStudyData);
    showStage('stage-practice');
  });

  // STAGE 6: PRACTICE
  function renderPracticeStage(data) {
    const practice = data.practice || {};
    practiceExerciseTitle.textContent = practice.title || 'Implement Core Functionality';
    practiceProblemStatement.textContent = practice.problem_statement || 'Write a Python function that solves the target challenge.';
    
    if (practice.expected_output && practice.expected_output.trim()) {
      practiceExpectedOutput.textContent = practice.expected_output;
      practiceExpectedContainer.classList.remove('hidden');
    } else {
      practiceExpectedContainer.classList.add('hidden');
    }

    starterPracticeCodeBackup = practice.starter_code || 'def solve():\n    # Implement solution\n    pass';
    practiceCodeArea.value = starterPracticeCodeBackup;

    // Reset console
    practiceConsoleContainer.classList.add('hidden');
    practiceConsoleOutput.textContent = '';
    practiceConsoleOutput.classList.remove('error');

    practiceHintsList.innerHTML = '';
    (practice.hints || ['Use dictionary lookup or counter', 'Ensure return type matches expected output']).forEach(h => {
      const li = document.createElement('li');
      li.textContent = h;
      practiceHintsList.appendChild(li);
    });
  }

  resetCodeBtn.addEventListener('click', () => {
    practiceCodeArea.value = starterPracticeCodeBackup;
    practiceConsoleContainer.classList.add('hidden');
    practiceConsoleOutput.textContent = '';
  });

  clearConsoleBtn.addEventListener('click', () => {
    practiceConsoleContainer.classList.add('hidden');
    practiceConsoleOutput.textContent = '';
  });

  // Run Code in Sandbox Subprocess
  runCodeBtn.addEventListener('click', async () => {
    const codeToRun = practiceCodeArea.value.trim();
    if (!codeToRun) {
      showError('Please write some Python code before running.');
      return;
    }

    hideError();
    setLoading(runCodeBtn, true, 'Running Code...');

    try {
      const res = await fetch('/execute-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: practiceCodeArea.value,
          timeout_seconds: 5
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Code execution failed on server.');

      practiceConsoleContainer.classList.remove('hidden');

      if (data.success) {
        consoleStatusIndicator.className = 'status-indicator success';
        consoleStatusIndicator.textContent = '✓ Execution Succeeded (Exit Code 0)';
        practiceConsoleOutput.className = 'console-output';
        practiceConsoleOutput.textContent = data.stdout || '(Program completed successfully with no stdout output)';
      } else {
        consoleStatusIndicator.className = 'status-indicator error';
        consoleStatusIndicator.textContent = '✗ Execution Failed (Exit Code ' + data.exit_code + ')';
        practiceConsoleOutput.className = 'console-output error';
        practiceConsoleOutput.textContent = (data.stderr || data.error || 'Execution encountered an error.') + (data.stdout ? '\n\n--- Standard Output ---\n' + data.stdout : '');
      }
    } catch (err) {
      practiceConsoleContainer.classList.remove('hidden');
      consoleStatusIndicator.className = 'status-indicator error';
      consoleStatusIndicator.textContent = '✗ Execution Error';
      practiceConsoleOutput.className = 'console-output error';
      practiceConsoleOutput.textContent = err.message;
    } finally {
      setLoading(runCodeBtn, false, '▶ Run Code');
    }
  });

  submitPracticeBtn.addEventListener('click', async () => {
    hideError();
    setLoading(submitPracticeBtn, true, 'Evaluating & Running LangGraph...');

    const submittedCode = practiceCodeArea.value;

    try {
      const res = await fetch('/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: currentStudentId,
          learning_goal: activeStudyData.learning_goal,
          practice_code: submittedCode,
          action: 'practice_submit'
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error evaluating practice code.');

      activeStudyData = data;
      renderPerformanceStage(data);
      showStage('stage-performance');
      loadProgressAndHistory();
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(submitPracticeBtn, false, 'Submit Solution for Evaluation →');
    }
  });

  // STAGE 7: PERFORMANCE & ROUTING
  function renderPerformanceStage(data) {
    const evalData = data.evaluation || {};
    const perfData = data.performance || {};
    const routing = (data.routing_decision || 'ADVANCE').toUpperCase();

    perfQuizScore.textContent = (evalData.quiz_score !== undefined ? evalData.quiz_score : 80) + '%';
    perfPracticeScore.textContent = (evalData.score || 85) + '%';
    perfOverallScore.textContent = (perfData.current_score || 82) + '%';
    perfPaceStatus.textContent = (perfData.pace_status || 'on_track').replace('_', ' ').toUpperCase();

    perfStrongList.innerHTML = '';
    (perfData.strong_topics || [data.current_topic + ' Syntax & Primitives']).forEach(t => {
      const li = document.createElement('li');
      li.textContent = t;
      perfStrongList.appendChild(li);
    });

    perfWeakList.innerHTML = '';
    (perfData.weak_topics || ['Return values & edge conditions']).forEach(t => {
      const li = document.createElement('li');
      li.textContent = t;
      perfWeakList.appendChild(li);
    });

    evaluatorFeedbackText.textContent = evalData.feedback || 'Good implementation of core requirements.';

    routingDecisionPill.className = 'routing-pill';
    if (routing === 'ADVANCE') {
      routingDecisionPill.classList.add('pill-advance');
      routingDecisionPill.textContent = '🟢 ADVANCE';
      routingDecisionText.textContent = 'Mastery demonstrated! Ready to advance to the next roadmap milestone.';
      nextTaskBtnText.textContent = 'Advance to Next Topic →';
      plannerUpdateBox.classList.add('hidden');
    } else if (routing === 'REINFORCE') {
      routingDecisionPill.classList.add('pill-reinforce');
      routingDecisionPill.textContent = '🟡 REINFORCE';
      routingDecisionText.textContent = 'Partial mastery detected. System will reinforce concepts with targeted re-teaching.';
      nextTaskBtnText.textContent = 'Review & Reinforce Topic →';
      plannerUpdateBox.classList.add('hidden');
    } else {
      routingDecisionPill.classList.add('pill-replan');
      routingDecisionPill.textContent = '🔵 FULL REPLAN';
      routingDecisionText.textContent = 'Substantial gaps detected. Planner Update Agent has dynamically reorganized the remaining roadmap.';
      nextTaskBtnText.textContent = 'Continue with Updated Plan →';

      if (data.planner_update) {
        plannerUpdateBox.classList.remove('hidden');
        plannerUpdateText.textContent = data.planner_update.changes_summary || 'Injected foundational remediation module.';
      }
    }

    workflowStepsFlow.innerHTML = '';
    (data.workflow_history || ['Assessment', 'Plan', 'Tutor', 'Quiz', 'Practice', 'Evaluation', 'Performance', routing]).forEach(step => {
      const pill = document.createElement('span');
      pill.className = 'badge badge-primary';
      pill.textContent = step;
      workflowStepsFlow.appendChild(pill);
    });
  }

  nextTaskBtn.addEventListener('click', () => {
    renderPlanStage(activeStudyData);
    renderLearnStage(activeStudyData);
    showStage('stage-learn');
  });

  async function loadProgressAndHistory() {
    try {
      const [progRes, histRes] = await Promise.all([
        fetch('/progress?student_id=' + currentStudentId),
        fetch('/history?student_id=' + currentStudentId + '&limit=10')
      ]);

      if (progRes.ok) {
        const progData = await progRes.json();
        renderMastery(progData.mastery_records || []);
      }

      if (histRes.ok) {
        const histData = await histRes.json();
        renderSessions(histData || []);
      }
    } catch (e) {
      console.warn('Error loading persistent history:', e);
    }
  }

  function renderMastery(records) {
    masteryBadges.innerHTML = '';
    if (records.length === 0) {
      masteryBadges.innerHTML = '<small class="text-muted">No mastery records yet.</small>';
      return;
    }
    records.forEach(r => {
      const span = document.createElement('span');
      span.className = 'mastery-pill ' + r.status;
      span.textContent = r.topic_name + ' (' + r.score + '%)';
      masteryBadges.appendChild(span);
    });
  }

  function renderSessions(sessions) {
    sessionsHistoryList.innerHTML = '';
    if (sessions.length === 0) {
      sessionsHistoryList.innerHTML = '<li class="empty-msg">No previous sessions recorded yet.</li>';
      return;
    }
    sessions.forEach(s => {
      const li = document.createElement('li');
      li.className = 'session-item';
      li.innerHTML = '<span>' + escapeHtml(s.topic || 'Session') + '</span><strong>' + (s.overall_score || 0) + '% [' + (s.routing_decision || 'ADVANCE') + ']</strong>';
      sessionsHistoryList.appendChild(li);
    });
  }

  function setLoading(btn, isLoading, text) {
    if (!btn) return;
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    if (isLoading) {
      btn.disabled = true;
      if (btnText) btnText.textContent = text;
      if (spinner) spinner.classList.remove('hidden');
    } else {
      btn.disabled = false;
      if (btnText) btnText.textContent = text;
      if (spinner) spinner.classList.add('hidden');
    }
  }

  function showError(msg) {
    errorBanner.textContent = msg;
    errorBanner.classList.remove('hidden');
  }

  function hideError() {
    errorBanner.classList.add('hidden');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
