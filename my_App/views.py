from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
import random

from .forms import CustomUserRegistrationForm, RecruiterProfileForm, JobSeekerProfileForm, JobPostForm
from .models import UserProfile, Job, JobApplication

# ---------------- Home ----------------
def home(request):
    return render(request, 'jobportal/home.html')


# ---------------- Registration ----------------
def register(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'jobportal/register.html', {'form': form})


# ---------------- Login ----------------
def user_login(request):
    if request.method == 'POST':
        login_input = request.POST['username']  # can be username or email
        password = request.POST['password']

        # Authenticate by username
        user = authenticate(request, username=login_input, password=password)

        # If username fails, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'jobportal/login.html')


# ---------------- Logout ----------------
def user_logout(request):
    logout(request)
    return redirect('home')


# ---------------- Dashboard ----------------
@login_required
def dashboard(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile.')
        return redirect('profile')
    
    context = {'profile': profile}
    
    if profile.user_type == 'recruiter':
        context['jobs'] = Job.objects.filter(recruiter=profile)
    else:
        # Job seeker dashboard with skill matching
        user_skills = profile.get_skills_list()
        matched_jobs = []
        if user_skills:
            for job in Job.objects.all():
                job_skills = job.get_required_skills_list()
                matches = set(user_skills) & set(job_skills)
                if matches:
                    matched_jobs.append({
                        'job': job,
                        'matched_skills': list(matches),
                        'match_percentage': len(matches) / len(job_skills) * 100 if job_skills else 0
                    })
            matched_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
        context['matched_jobs'] = matched_jobs[:5]  # Top 5 matches
    
    return render(request, 'jobportal/dashboard.html', context)


# ---------------- Profile ----------------
@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user,
            display_name=request.user.username,
            user_type='jobseeker'
        )

    if request.method == 'POST':
        # Pass request.FILES to handle image/resume uploads
        if profile.user_type == 'recruiter':
            form = RecruiterProfileForm(request.POST, request.FILES, instance=profile)
        else:
            form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        if profile.user_type == 'recruiter':
            form = RecruiterProfileForm(instance=profile)
        else:
            form = JobSeekerProfileForm(instance=profile)

    return render(request, 'jobportal/profile.html', {'form': form, 'profile': profile})


# ---------------- Job Posting ----------------
@login_required
def post_job(request):
    try:
        profile = request.user.userprofile
        if profile.user_type != 'recruiter':
            messages.error(request, 'Only recruiters can post jobs.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = profile
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('dashboard')
    else:
        form = JobPostForm()
    
    return render(request, 'jobportal/post_job.html', {'form': form})


# ---------------- Job List ----------------
def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    
    search_query = request.GET.get('search')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(required_skills__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    category = request.GET.get('category')
    if category:
        jobs = jobs.filter(category=category)
    
    context = {
        'jobs': jobs,
        'search_query': search_query,
        'selected_category': category,
        'categories': Job.CATEGORY_CHOICES,
    }
    
    return render(request, 'jobportal/job_list.html', context)


# ---------------- Apply Job ----------------
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    try:
        profile = request.user.userprofile
        if profile.user_type != 'jobseeker':
            messages.error(request, 'Only job seekers can apply for jobs.')
            return redirect('job_list')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    already_applied = JobApplication.objects.filter(job=job, applicant=profile).exists()
    
    if request.method == 'POST' and not already_applied:
        JobApplication.objects.create(job=job, applicant=profile)
        messages.success(request, f'Successfully applied for {job.title}!')
        return redirect('my_applications')
    
    user_skills = profile.get_skills_list()
    job_skills = job.get_required_skills_list()
    matched_skills = list(set(user_skills) & set(job_skills))
    match_percentage = len(matched_skills) / len(job_skills) * 100 if job_skills else 0
    
    context = {
        'job': job,
        'profile': profile,
        'already_applied': already_applied,
        'matched_skills': matched_skills,
        'match_percentage': match_percentage,
    }
    
    return render(request, 'jobportal/apply_job.html', context)


# ---------------- My Applications ----------------
@login_required
def my_applications(request):
    try:
        profile = request.user.userprofile
        if profile.user_type != 'jobseeker':
            messages.error(request, 'Only job seekers can view applications.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    applications = JobApplication.objects.filter(applicant=profile).order_by('-applied_at')
    
    return render(request, 'jobportal/my_applications.html', {
        'applications': applications,
        'profile': profile
    })


# ---------------- Job Applications (Recruiter) ----------------
@login_required
def job_applications(request, job_id=None):
    try:
        profile = request.user.userprofile
        if profile.user_type != 'recruiter':
            messages.error(request, 'Only recruiters can view job applications.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    if job_id:
        job = get_object_or_404(Job, id=job_id, recruiter=profile)
        applications = JobApplication.objects.filter(job=job).order_by('-applied_at')
        return render(request, 'jobportal/job_applications.html', {
            'job': job,
            'applications': applications,
            'profile': profile
        })
    else:
        recruiter_jobs = Job.objects.filter(recruiter=profile)
        applications = JobApplication.objects.filter(job__in=recruiter_jobs).order_by('-applied_at')
        return render(request, 'jobportal/all_applications.html', {
            'applications': applications,
            'profile': profile,
            'recruiter_jobs': recruiter_jobs
        })


# ---------------- Skill Match ----------------
@login_required
def skill_match(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    matched_jobs = []
    
    if profile.user_type == 'jobseeker':
        user_skills = profile.get_skills_list()
        if user_skills:
            for job in Job.objects.all():
                job_skills = job.get_required_skills_list()
                matches = set(user_skills) & set(job_skills)
                if matches:
                    matched_jobs.append({
                        'job': job,
                        'matched_skills': list(matches),
                        'match_percentage': len(matches) / len(job_skills) * 100 if job_skills else 0
                    })
            matched_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
    elif profile.user_type == 'recruiter':
        recruiter_jobs = Job.objects.filter(recruiter=profile)
        for job in recruiter_jobs:
            job_skills = job.get_required_skills_list()
            if job_skills:
                for seeker_profile in UserProfile.objects.filter(user_type='jobseeker'):
                    seeker_skills = seeker_profile.get_skills_list()
                    matches = set(job_skills) & set(seeker_skills)
                    if matches:
                        matched_jobs.append({
                            'job': job,
                            'seeker': seeker_profile,
                            'matched_skills': list(matches),
                            'match_percentage': len(matches) / len(job_skills) * 100
                        })
        matched_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    return render(request, 'jobportal/skill_match.html', {
        'matched_jobs': matched_jobs,
        'profile': profile
    })


# ---------------- Forgot Password Flow ----------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            otp = random.randint(1000, 9999)
            cache.set(email, otp, timeout=300)  # OTP valid for 5 min
            try:
                send_mail(
                    'Forgot Password OTP',
                    f"Your OTP is: {otp}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                return render(request, 'forgot_password/password_reset_request.html', {'error': f'Email sending failed: {e}'})
            request.session['reset_email'] = email
            return redirect('otp_verify')
        else:
            return render(request, 'forgot_password/password_reset_request.html', {'error': 'Email not found'})
    return render(request, 'forgot_password/password_reset_request.html')


def otp_verify(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    if request.method == "POST":
        input_otp = request.POST.get('otp')
        cached_otp = cache.get(email)
        if str(input_otp) == str(cached_otp):
            cache.set(f'otp_verified_{email}', True, timeout=300)
            return redirect('reset_password')
        else:
            return render(request, 'forgot_password/otp_verify.html', {'error': 'Invalid OTP'})
    return render(request, 'forgot_password/otp_verify.html')


def reset_password(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    otp_verified = cache.get(f'otp_verified_{email}')
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not otp_verified:
            return render(request, 'forgot_password/reset_password.html', {'error': 'OTP verification required'})
        if new_password != confirm_password:
            return render(request, 'forgot_password/reset_password.html', {'error': 'Passwords do not match'})
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        request.session.pop('reset_email', None)
        cache.delete(f'otp_verified_{email}')
        cache.delete(email)
        return redirect('login')
    return render(request, 'forgot_password/reset_password.html')
