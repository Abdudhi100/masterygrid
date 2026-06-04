from rest_framework import serializers


class TeacherOverviewSerializer(serializers.Serializer):
    total_assignments_created = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    draft_assignments = serializers.IntegerField()
    closed_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    average_score_percentage = serializers.FloatField()
    recent_assignments = serializers.ListField()
    recent_low_performing_students = serializers.ListField()
    weak_topics_summary = serializers.ListField()


class AssignmentResultsSerializer(serializers.Serializer):
    assignment = serializers.DictField()
    submission_summary = serializers.DictField()
    student_results = serializers.ListField()
    question_performance = serializers.ListField()
    most_missed_questions = serializers.ListField()


class WeakStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    class_arm = serializers.CharField(allow_null=True)
    average_percentage = serializers.FloatField()
    graded_submission_count = serializers.IntegerField()
    missed_assignment_count = serializers.IntegerField()
    weak_topics = serializers.ListField()
    risk_level = serializers.CharField()
    recommendation = serializers.CharField()


class WeakTopicSerializer(serializers.Serializer):
    subject = serializers.CharField()
    topic = serializers.CharField()
    class_arm = serializers.CharField()
    average_percentage = serializers.FloatField()
    total_submissions = serializers.IntegerField()
    weak_student_count = serializers.IntegerField()
    recommendation = serializers.CharField()


class StudentPerformanceSerializer(serializers.Serializer):
    student = serializers.DictField()
    assignments_attempted = serializers.IntegerField()
    average_percentage = serializers.FloatField()
    performance_by_subject = serializers.ListField()
    performance_by_topic = serializers.ListField()
    recent_scores = serializers.ListField()
    weak_topics = serializers.ListField()
    missed_assignments = serializers.ListField()
    recommendation = serializers.CharField()


class RemediationAffectedStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    admission_number = serializers.CharField(allow_null=True)
    class_arm = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    average_score = serializers.FloatField()
    attempted_count = serializers.IntegerField()


class RemediationActionPayloadSerializer(serializers.Serializer):
    class_arm = serializers.IntegerField()
    subject = serializers.IntegerField()
    topic = serializers.IntegerField()
    question_count = serializers.IntegerField()
    title = serializers.CharField()
    instructions = serializers.CharField(allow_blank=True)
    remedial = serializers.BooleanField()


class RemediationTopicCardSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic = serializers.CharField()
    class_arm_id = serializers.IntegerField()
    class_arm = serializers.CharField()
    class_level_id = serializers.IntegerField()
    class_level = serializers.CharField()
    average_score = serializers.FloatField()
    attempted_count = serializers.IntegerField()
    weak_student_count = serializers.IntegerField()
    available_approved_questions = serializers.IntegerField()
    recommended_question_count = serializers.IntegerField()
    suggested_assignment_title = serializers.CharField()
    suggested_instructions = serializers.CharField()
    recommended_action = serializers.CharField()
    priority = serializers.CharField()
    latest_assignment_id = serializers.IntegerField()
    latest_assignment_title = serializers.CharField()
    latest_assignment_created_at = serializers.DateTimeField()
    affected_students = RemediationAffectedStudentSerializer(many=True)
    action_payload = RemediationActionPayloadSerializer()


class RemediationSummarySerializer(serializers.Serializer):
    total_weak_topics = serializers.IntegerField()
    actionable_topic_count = serializers.IntegerField()
    total_affected_students = serializers.IntegerField()
    total_graded_submissions = serializers.IntegerField()
    average_score = serializers.FloatField()
    message = serializers.CharField()


class TeacherRemediationPlanSerializer(serializers.Serializer):
    summary = RemediationSummarySerializer()
    recommended_actions = RemediationTopicCardSerializer(many=True)
    weak_topic_cards = RemediationTopicCardSerializer(many=True)
    affected_students = RemediationAffectedStudentSerializer(many=True)


class AdminOverviewSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_class_arms = serializers.IntegerField()
    total_subjects = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    draft_assignments = serializers.IntegerField()
    closed_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    pending_or_not_started_submissions = serializers.IntegerField()
    average_school_percentage = serializers.FloatField()
    weak_students_count = serializers.IntegerField()
    weak_classes_count = serializers.IntegerField()
    weak_subjects_count = serializers.IntegerField()
    recent_assignments = serializers.ListField()
    recent_low_performing_students = serializers.ListField()


class AdminClassPerformanceSerializer(serializers.Serializer):
    class_arm_id = serializers.IntegerField()
    class_level = serializers.CharField()
    class_arm_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    average_percentage = serializers.FloatField()
    submission_rate = serializers.FloatField()
    weak_student_count = serializers.IntegerField()
    risk_level = serializers.CharField()
    recommendation = serializers.CharField()


class AdminSubjectPerformanceSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    total_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    average_percentage = serializers.FloatField()
    weak_topic_count = serializers.IntegerField()
    weakest_topics = serializers.ListField()
    risk_level = serializers.CharField()
    recommendation = serializers.CharField()


class AdminTeacherActivitySerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    staff_id = serializers.CharField(allow_null=True)
    assigned_classes_count = serializers.IntegerField()
    assigned_subjects_count = serializers.IntegerField()
    assignments_created = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    total_student_submissions = serializers.IntegerField()
    average_class_performance = serializers.FloatField()
    last_assignment_date = serializers.DateTimeField(allow_null=True)
    activity_status = serializers.CharField()
    recommendation = serializers.CharField()


class AdminWeakStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    admission_number = serializers.CharField(allow_null=True)
    class_arm = serializers.CharField(allow_null=True)
    average_percentage = serializers.FloatField()
    graded_submission_count = serializers.IntegerField()
    missed_assignment_count = serializers.IntegerField()
    weak_subjects = serializers.ListField()
    weak_topics = serializers.ListField()
    risk_level = serializers.CharField()
    recommendation = serializers.CharField()


class AdminAssignmentComplianceSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    title = serializers.CharField()
    teacher_name = serializers.CharField()
    class_arm = serializers.CharField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    status = serializers.CharField()
    due_at = serializers.DateTimeField(allow_null=True)
    deadline_status = serializers.CharField()
    expected_students = serializers.IntegerField()
    started_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    graded_count = serializers.IntegerField()
    late_submission_count = serializers.IntegerField()
    not_started_count = serializers.IntegerField()
    submission_rate = serializers.FloatField()
    compliance_status = serializers.CharField()


class AdminInterventionActionPayloadSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()
    params = serializers.DictField()


class AdminInterventionSummarySerializer(serializers.Serializer):
    total_classes_at_risk = serializers.IntegerField()
    total_subjects_at_risk = serializers.IntegerField()
    total_teachers_at_risk = serializers.IntegerField()
    total_weak_student_clusters = serializers.IntegerField()
    total_compliance_alerts = serializers.IntegerField()
    total_urgent_interventions = serializers.IntegerField()
    average_school_percentage = serializers.FloatField()
    overall_risk_level = serializers.CharField()
    message = serializers.CharField()


class AdminUrgentInterventionSerializer(serializers.Serializer):
    category = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    risk_level = serializers.CharField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminClassInterventionSerializer(serializers.Serializer):
    class_arm_id = serializers.IntegerField()
    class_arm_name = serializers.CharField()
    class_level = serializers.CharField()
    average_score = serializers.FloatField()
    submitted_count = serializers.IntegerField()
    weak_student_count = serializers.IntegerField()
    risk_level = serializers.CharField()
    main_weak_subjects = serializers.ListField()
    main_weak_topics = serializers.ListField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminSubjectInterventionSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    average_score = serializers.FloatField()
    weak_class_count = serializers.IntegerField()
    weak_student_count = serializers.IntegerField()
    affected_class_arms = serializers.ListField(child=serializers.CharField())
    risk_level = serializers.CharField()
    weakest_topics = serializers.ListField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminTeacherInterventionSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    teacher_email = serializers.EmailField(allow_blank=True)
    staff_id = serializers.CharField(allow_null=True)
    classes_subjects_taught = serializers.ListField()
    assignment_count = serializers.IntegerField()
    published_assignment_count = serializers.IntegerField()
    average_class_score = serializers.FloatField()
    submission_rate = serializers.FloatField()
    submitted_count = serializers.IntegerField()
    expected_submission_count = serializers.IntegerField()
    risk_level = serializers.CharField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminWeakStudentClusterSerializer(serializers.Serializer):
    class_arm = serializers.CharField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    weak_student_count = serializers.IntegerField()
    average_score = serializers.FloatField()
    risk_level = serializers.CharField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminAssignmentComplianceAlertSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    title = serializers.CharField()
    teacher_name = serializers.CharField()
    class_arm = serializers.CharField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    expected_students = serializers.IntegerField()
    started_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    not_started_count = serializers.IntegerField()
    submission_rate = serializers.FloatField()
    risk_level = serializers.CharField()
    recommended_action = serializers.CharField()
    action_payload = AdminInterventionActionPayloadSerializer()


class AdminInterventionDashboardSerializer(serializers.Serializer):
    summary = AdminInterventionSummarySerializer()
    risk_score = serializers.IntegerField()
    overall_risk_level = serializers.CharField()
    urgent_interventions = AdminUrgentInterventionSerializer(many=True)
    class_interventions = AdminClassInterventionSerializer(many=True)
    subject_interventions = AdminSubjectInterventionSerializer(many=True)
    teacher_interventions = AdminTeacherInterventionSerializer(many=True)
    weak_student_clusters = AdminWeakStudentClusterSerializer(many=True)
    assignment_compliance_alerts = AdminAssignmentComplianceAlertSerializer(many=True)
    recommended_actions = AdminUrgentInterventionSerializer(many=True)


class StudentDashboardSummarySerializer(serializers.Serializer):
    pending_assignments_count = serializers.IntegerField()
    overdue_assignments_count = serializers.IntegerField()
    due_soon_assignments_count = serializers.IntegerField()
    graded_assignments_count = serializers.IntegerField()
    assignment_average = serializers.FloatField()
    practice_sessions_count = serializers.IntegerField()
    practice_average = serializers.FloatField()
    unread_notifications_count = serializers.IntegerField()


class StudentDashboardAssignmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    subject_name = serializers.CharField()
    topic_title = serializers.CharField()
    class_arm_name = serializers.CharField()
    question_count = serializers.IntegerField()
    duration_minutes = serializers.IntegerField(allow_null=True)
    starts_at = serializers.DateTimeField(allow_null=True)
    due_at = serializers.DateTimeField(allow_null=True)
    original_due_at = serializers.DateTimeField(allow_null=True)
    allow_late_submissions = serializers.BooleanField()
    late_submission_deadline = serializers.DateTimeField(allow_null=True)
    deadline_status = serializers.CharField()
    is_overdue = serializers.BooleanField()
    is_due_soon = serializers.BooleanField()
    can_submit_now = serializers.BooleanField()
    submission_id = serializers.IntegerField(allow_null=True)
    submission_status = serializers.CharField(allow_null=True)
    is_late = serializers.BooleanField()
    submitted_after_due_seconds = serializers.IntegerField(allow_null=True)
    href = serializers.CharField()


class StudentDashboardRecentResultSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()
    assignment_id = serializers.IntegerField()
    assignment_title = serializers.CharField()
    subject_name = serializers.CharField()
    topic_title = serializers.CharField()
    score = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    percentage = serializers.FloatField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    graded_at = serializers.DateTimeField(allow_null=True)
    is_late = serializers.BooleanField()
    href = serializers.CharField()


class StudentDashboardAssignmentsSerializer(serializers.Serializer):
    pending = StudentDashboardAssignmentSerializer(many=True)
    due_soon = StudentDashboardAssignmentSerializer(many=True)
    overdue = StudentDashboardAssignmentSerializer(many=True)
    recently_graded = StudentDashboardRecentResultSerializer(many=True)


class StudentDashboardPracticeSerializer(serializers.Serializer):
    recent_sessions = serializers.ListField()
    average = serializers.FloatField()
    weak_topics = serializers.ListField()
    strong_topics = serializers.ListField()


class StudentDashboardLearningPathSerializer(serializers.Serializer):
    overall_status = serializers.CharField()
    headline = serializers.CharField()
    message = serializers.CharField()
    recommended_next_action = serializers.JSONField(allow_null=True)
    top_topic_card = serializers.JSONField(allow_null=True)


class StudentDashboardNotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    message = serializers.CharField(allow_blank=True)
    notification_type = serializers.CharField()
    priority = serializers.CharField()
    status = serializers.CharField()
    target_url = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()


class StudentDashboardQuickActionSerializer(serializers.Serializer):
    title = serializers.CharField()
    href = serializers.CharField()
    priority = serializers.CharField()


class StudentDashboardSerializer(serializers.Serializer):
    summary = StudentDashboardSummarySerializer()
    assignments = StudentDashboardAssignmentsSerializer()
    practice = StudentDashboardPracticeSerializer()
    learning_path = StudentDashboardLearningPathSerializer()
    notifications = StudentDashboardNotificationSerializer(many=True)
    quick_actions = StudentDashboardQuickActionSerializer(many=True)


class StudentProgressProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    admission_number = serializers.CharField(allow_null=True)
    class_arm = serializers.CharField(allow_null=True)
    class_arm_id = serializers.IntegerField(allow_null=True)
    class_level = serializers.CharField(allow_null=True)
    class_level_id = serializers.IntegerField(allow_null=True)
    school = serializers.CharField(allow_null=True)
    school_id = serializers.IntegerField(allow_null=True)


class StudentProgressSummarySerializer(serializers.Serializer):
    assignment_average = serializers.FloatField()
    practice_average = serializers.FloatField()
    overall_average = serializers.FloatField()
    graded_assignments_count = serializers.IntegerField()
    missed_assignments_count = serializers.IntegerField()
    practice_sessions_count = serializers.IntegerField()
    weak_topic_count = serializers.IntegerField()
    strong_topic_count = serializers.IntegerField()
    risk_level = serializers.CharField()


class StudentProgressAssignmentResultSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()
    assignment_id = serializers.IntegerField()
    assignment_title = serializers.CharField()
    teacher_name = serializers.CharField()
    class_arm = serializers.CharField()
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    score = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    percentage = serializers.FloatField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    graded_at = serializers.DateTimeField(allow_null=True)


class StudentProgressSubjectBreakdownSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    average_percentage = serializers.FloatField()
    graded_assignments_count = serializers.IntegerField(required=False)
    sessions_completed = serializers.IntegerField(required=False)
    questions_answered = serializers.IntegerField(required=False)
    correct_answers = serializers.IntegerField(required=False)
    last_graded_at = serializers.DateTimeField(allow_null=True, required=False)
    last_practiced_at = serializers.DateTimeField(allow_null=True, required=False)


class StudentProgressTopicBreakdownSerializer(StudentProgressSubjectBreakdownSerializer):
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()


class StudentProgressMissedAssignmentSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    title = serializers.CharField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    due_at = serializers.DateTimeField(allow_null=True)


class StudentProgressPracticeSessionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField(allow_null=True)
    topic_title = serializers.CharField(allow_null=True)
    class_level_id = serializers.IntegerField(allow_null=True)
    class_level_name = serializers.CharField(allow_null=True)
    difficulty = serializers.CharField()
    question_count_requested = serializers.IntegerField()
    score = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    percentage = serializers.FloatField()
    submitted_at = serializers.DateTimeField(allow_null=True)


class StudentProgressTopicSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    assignment_average = serializers.FloatField(allow_null=True)
    practice_average = serializers.FloatField(allow_null=True)
    assignment_count = serializers.IntegerField()
    practice_sessions_count = serializers.IntegerField()
    average_percentage = serializers.FloatField()
    evidence_count = serializers.IntegerField()


class StudentProgressRecommendationSerializer(serializers.Serializer):
    recommended_action = serializers.CharField()
    subject_id = serializers.IntegerField(allow_null=True)
    subject_name = serializers.CharField(allow_blank=True)
    topic_id = serializers.IntegerField(allow_null=True)
    topic_title = serializers.CharField(allow_blank=True)
    reason = serializers.CharField()
    action_payload = serializers.DictField()


class StudentProgressAssignmentPerformanceSerializer(serializers.Serializer):
    recent_results = StudentProgressAssignmentResultSerializer(many=True)
    subject_breakdown = StudentProgressSubjectBreakdownSerializer(many=True)
    topic_breakdown = StudentProgressTopicBreakdownSerializer(many=True)
    missed_assignments = StudentProgressMissedAssignmentSerializer(many=True)


class StudentProgressPracticePerformanceSerializer(serializers.Serializer):
    recent_sessions = StudentProgressPracticeSessionSerializer(many=True)
    subject_breakdown = StudentProgressSubjectBreakdownSerializer(many=True)
    topic_breakdown = StudentProgressTopicBreakdownSerializer(many=True)


class StudentProgressLearningPathSummarySerializer(serializers.Serializer):
    overall_status = serializers.CharField()
    headline = serializers.CharField()
    message = serializers.CharField()
    recommended_next_action = serializers.DictField(allow_null=True)


class StudentProgressReportSerializer(serializers.Serializer):
    student = StudentProgressProfileSerializer()
    summary = StudentProgressSummarySerializer()
    assignment_performance = StudentProgressAssignmentPerformanceSerializer()
    practice_performance = StudentProgressPracticePerformanceSerializer()
    weak_topics = StudentProgressTopicSerializer(many=True)
    strong_topics = StudentProgressTopicSerializer(many=True)
    recommendations = StudentProgressRecommendationSerializer(many=True)
    learning_path_summary = StudentProgressLearningPathSummarySerializer()
    generated_at = serializers.DateTimeField()
