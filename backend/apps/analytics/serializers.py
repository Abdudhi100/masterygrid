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
    expected_students = serializers.IntegerField()
    started_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    graded_count = serializers.IntegerField()
    not_started_count = serializers.IntegerField()
    submission_rate = serializers.FloatField()
    compliance_status = serializers.CharField()
