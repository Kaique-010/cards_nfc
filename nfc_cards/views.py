from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import DetailView, CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from .models import Person, Pet, NFCCard, Empresa, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """Formulário customizado para registro de usuário"""
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    email = forms.EmailField(required=True, label="E-mail")
    telefone = forms.CharField(max_length=20, required=False, label="Telefone")
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Atualizar o perfil com telefone
            if hasattr(user, 'profile'):
                user.profile.telefone = self.cleaned_data.get("telefone", "")
                user.profile.save()
        return user

class EmpresaCreationForm(forms.ModelForm):
    """Formulário para criação de empresa"""
    class Meta:
        model = Empresa
        fields = ['nome', 'descricao', 'email', 'telefone', 'website', 'endereco', 
                 'cor_primaria', 'cor_secundaria', 'logo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'endereco': forms.Textarea(attrs={'rows': 3}),
            'cor_primaria': forms.TextInput(attrs={'type': 'color'}),
            'cor_secundaria': forms.TextInput(attrs={'type': 'color'}),
        }

def register_view(request):
    """View para registro de novo usuário"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Agora você pode fazer login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def create_empresa_view(request):
    """View para criação de empresa (apenas para usuários logados sem empresa)"""
    # Verificar se o usuário já tem empresa
    try:
        if request.user.profile.empresa:
            messages.info(request, 'Você já possui uma empresa cadastrada.')
            return redirect('minha_empresa')
    except (UserProfile.DoesNotExist, AttributeError):
        pass  # Usuário não tem perfil ainda, pode criar empresa
    
    if request.method == 'POST':
        form = EmpresaCreationForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save()
            # Criar ou atualizar o perfil do usuário
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.empresa = empresa
            user_profile.save()
            messages.success(request, f'Empresa "{empresa.nome}" criada com sucesso!')
            # Redirecionar diretamente para a empresa em vez de minha_empresa
            return redirect('empresa_home', empresa_slug=empresa.slug)
    else:
        form = EmpresaCreationForm()
    
    return render(request, 'nfc_cards/create_empresa.html', {'form': form})

@login_required
def minha_empresa_view(request):
    """View para a página da empresa do usuário logado"""
    try:
        user_profile = request.user.profile
        if not user_profile.empresa:
            messages.warning(request, 'Você precisa criar uma empresa primeiro.')
            return redirect('create_empresa')
        empresa = user_profile.empresa
        return redirect('empresa_home', empresa_slug=empresa.slug)
    except (UserProfile.DoesNotExist, AttributeError):
        messages.warning(request, 'Você precisa criar uma empresa primeiro.')
        return redirect('create_empresa')

@login_required
def dashboard_view(request):
    """Dashboard principal do usuário logado"""
    try:
        user_profile = request.user.profile
        if not user_profile.empresa:
            return redirect('create_empresa')
        empresa = user_profile.empresa
        
        context = {
            'empresa': empresa,
            'total_pessoas': empresa.pessoas.filter(ativo=True).count(),
            'total_pets': empresa.pets.filter(ativo=True).count(),
            'total_cartoes': empresa.cartoes_nfc.filter(ativo=True).count(),
            'pessoas_recentes': empresa.pessoas.filter(ativo=True).order_by('-criado_em')[:5],
            'pets_recentes': empresa.pets.filter(ativo=True).order_by('-criado_em')[:5],
        }
        return render(request, 'nfc_cards/dashboard.html', context)
    except (UserProfile.DoesNotExist, AttributeError):
        return redirect('create_empresa')
    
    context = {
        'empresa': empresa,
        'total_pessoas': empresa.pessoas.filter(ativo=True).count(),
        'total_pets': empresa.pets.filter(ativo=True).count(),
        'total_cartoes': empresa.cartoes_nfc.filter(ativo=True).count(),
        'pessoas_recentes': empresa.pessoas.filter(ativo=True).order_by('-criado_em')[:5],
        'pets_recentes': empresa.pets.filter(ativo=True).order_by('-criado_em')[:5],
    }
    return render(request, 'nfc_cards/dashboard.html', context)

# Mixin para verificar se o usuário tem acesso à empresa
class EmpresaAccessMixin(LoginRequiredMixin):
    """Mixin para verificar se o usuário tem acesso à empresa"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        empresa_slug = kwargs.get('empresa_slug')
        if empresa_slug:
            # Verificar se o usuário tem acesso a esta empresa
            try:
                if (not request.user.profile.empresa or 
                    request.user.profile.empresa.slug != empresa_slug):
                    messages.error(request, 'Você não tem acesso a esta empresa.')
                    return redirect('minha_empresa')
            except (UserProfile.DoesNotExist, AttributeError):
                messages.error(request, 'Você precisa criar uma empresa primeiro.')
                return redirect('create_empresa')
        
        return super().dispatch(request, *args, **kwargs)

# Atualizar as views existentes para incluir controle de acesso
class PersonDetailView(DetailView):
    model = Person
    template_name = 'nfc_cards/person_detail.html'
    context_object_name = 'person'
    slug_field = 'slug'
    slug_url_kwarg = 'person_slug'
    
    def get_object(self, queryset=None):
        empresa_slug = self.kwargs.get('empresa_slug')
        person_slug = self.kwargs.get('person_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return get_object_or_404(Person, empresa=empresa, slug=person_slug, ativo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cartoes_nfc'] = self.object.cartoes_nfc.filter(ativo=True)
        context['empresa'] = self.object.empresa
        return context

class PetDetailView(DetailView):
    model = Pet
    template_name = 'nfc_cards/pet_detail.html'
    context_object_name = 'pet'
    slug_field = 'slug'
    slug_url_kwarg = 'pet_slug'
    
    def get_object(self, queryset=None):
        empresa_slug = self.kwargs.get('empresa_slug')
        pet_slug = self.kwargs.get('pet_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return get_object_or_404(Pet, empresa=empresa, slug=pet_slug, ativo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cartoes_nfc'] = self.object.cartoes_nfc.filter(ativo=True)
        context['empresa'] = self.object.empresa
        return context

class PersonCreateView(EmpresaAccessMixin, CreateView):
    model = Person
    template_name = 'nfc_cards/person_form.html'
    fields = ['nome', 'email', 'telefone', 'whatsapp', 'cargo', 
              'apresentacao', 'foto', 'linkedin', 'instagram', 'facebook', 
              'website', 'linktree_url']
    
    def get_success_url(self):
        empresa_slug = self.kwargs.get('empresa_slug')
        return reverse_lazy('person_list', kwargs={'empresa_slug': empresa_slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_slug = self.kwargs.get('empresa_slug')
        context['empresa'] = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return context
    
    def form_valid(self, form):
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        form.instance.empresa = empresa
        messages.success(self.request, 'Pessoa cadastrada com sucesso!')
        return super().form_valid(form)

class PetCreateView(EmpresaAccessMixin, CreateView):
    model = Pet
    template_name = 'nfc_cards/pet_form.html'
    fields = ['nome', 'especie', 'raca', 'porte', 'cor', 'data_nascimento', 
              'foto', 'veterinario', 'telefone_veterinario', 'observacoes', 
              'medicamentos', 'alergias', 'tutor']
    
    def get_success_url(self):
        empresa_slug = self.kwargs.get('empresa_slug')
        return reverse_lazy('pet_list', kwargs={'empresa_slug': empresa_slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        context['empresa'] = empresa
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        # Filtrar tutores apenas da empresa atual
        form.fields['tutor'].queryset = Person.objects.filter(empresa=empresa, ativo=True)
        return form
    
    def form_valid(self, form):
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        form.instance.empresa = empresa
        messages.success(self.request, 'Pet cadastrado com sucesso!')
        return super().form_valid(form)

class PersonListView(EmpresaAccessMixin, ListView):
    model = Person
    template_name = 'nfc_cards/person_list.html'
    context_object_name = 'pessoas'
    paginate_by = 12
    
    def get_queryset(self):
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return Person.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_slug = self.kwargs.get('empresa_slug')
        context['empresa'] = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return context

class PetListView(EmpresaAccessMixin, ListView):
    model = Pet
    template_name = 'nfc_cards/pet_list.html'
    context_object_name = 'pets'
    paginate_by = 12
    
    def get_queryset(self):
        empresa_slug = self.kwargs.get('empresa_slug')
        empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return Pet.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_slug = self.kwargs.get('empresa_slug')
        context['empresa'] = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
        return context

def home(request):
    """Página inicial do sistema - lista empresas ativas"""
    if request.user.is_authenticated:
        # Se o usuário está logado, verificar se tem perfil e empresa
        try:
            user_profile = request.user.profile
            if user_profile.empresa:
                # Se o usuário tem uma empresa, redireciona para o dashboard
                return redirect('dashboard')
            else:
                # Se não tem empresa, redireciona para criar uma
                return redirect('create_empresa')
        except (AttributeError, UserProfile.DoesNotExist):
            # Se o User não tem profile ou não existe
            return redirect('create_empresa')
    else:
        # Se não está logado, mostra página inicial pública
        empresas = Empresa.objects.filter(ativo=True).order_by('nome')
        
        context = {
            'empresas': empresas,
            'total_pessoas': Person.objects.filter(ativo=True).count(),
            'total_pets': Pet.objects.filter(ativo=True).count(),
            'total_cartoes': NFCCard.objects.filter(ativo=True).count(),
        }
        return render(request, 'nfc_cards/home.html', context)

def empresa_home(request, empresa_slug):
    """Página inicial de uma empresa específica"""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    
    context = {
        'empresa': empresa,
        'total_pessoas': empresa.pessoas.filter(ativo=True).count(),
        'total_pets': empresa.pets.filter(ativo=True).count(),
        'total_cartoes': empresa.cartoes_nfc.filter(ativo=True).count(),
        'pessoas_recentes': empresa.pessoas.filter(ativo=True).order_by('-criado_em')[:5],
        'pets_recentes': empresa.pets.filter(ativo=True).order_by('-criado_em')[:5],
    }
    return render(request, 'nfc_cards/empresa_home.html', context)

def nfc_redirect(request, codigo):
    """Redireciona baseado no código NFC (compatibilidade)"""
    try:
        cartao = NFCCard.objects.get(codigo_nfc=codigo, ativo=True)
        if cartao.pessoa:
            return redirect('person_detail', 
                          empresa_slug=cartao.empresa.slug, 
                          person_slug=cartao.pessoa.slug)
        elif cartao.pet:
            return redirect('pet_detail', 
                          empresa_slug=cartao.empresa.slug, 
                          pet_slug=cartao.pet.slug)
        else:
            messages.error(request, 'Cartão NFC não está associado a nenhum cadastro.')
            return redirect('home')
    except NFCCard.DoesNotExist:
        messages.error(request, 'Código NFC não encontrado.')
        return redirect('home')

def nfc_redirect_empresa(request, empresa_slug, codigo):
    """Redireciona baseado no código NFC dentro de uma empresa"""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    try:
        cartao = NFCCard.objects.get(codigo_nfc=codigo, empresa=empresa, ativo=True)
        if cartao.pessoa:
            return redirect('person_detail', 
                          empresa_slug=empresa_slug, 
                          person_slug=cartao.pessoa.slug)
        elif cartao.pet:
            return redirect('pet_detail', 
                          empresa_slug=empresa_slug, 
                          pet_slug=cartao.pet.slug)
        else:
            messages.error(request, 'Cartão NFC não está associado a nenhum cadastro.')
            return redirect('empresa_home', empresa_slug=empresa_slug)
    except NFCCard.DoesNotExist:
        messages.error(request, 'Código NFC não encontrado.')
        return redirect('empresa_home', empresa_slug=empresa_slug)

def api_nfc_info(request, codigo):
    """API para retornar informações do cartão NFC em JSON (compatibilidade)"""
    try:
        cartao = NFCCard.objects.get(codigo_nfc=codigo, ativo=True)
        
        if cartao.pessoa:
            data = {
                'tipo': 'pessoa',
                'empresa': cartao.empresa.nome,
                'empresa_slug': cartao.empresa.slug,
                'nome': cartao.pessoa.nome,
                'email': cartao.pessoa.email,
                'telefone': cartao.pessoa.telefone,
                'cargo': cartao.pessoa.cargo,
                'apresentacao': cartao.pessoa.apresentacao,
                'url': request.build_absolute_uri(cartao.pessoa.get_absolute_url()),
                'foto': cartao.pessoa.foto.url if cartao.pessoa.foto else None,
            }
        elif cartao.pet:
            data = {
                'tipo': 'pet',
                'empresa': cartao.empresa.nome,
                'empresa_slug': cartao.empresa.slug,
                'nome': cartao.pet.nome,
                'especie': cartao.pet.get_especie_display(),
                'raca': cartao.pet.raca,
                'tutor': cartao.pet.tutor.nome,
                'tutor_telefone': cartao.pet.tutor.telefone,
                'url': request.build_absolute_uri(cartao.pet.get_absolute_url()),
                'foto': cartao.pet.foto.url if cartao.pet.foto else None,
            }
        else:
            return JsonResponse({'error': 'Cartão não associado'}, status=404)
            
        return JsonResponse(data)
        
    except NFCCard.DoesNotExist:
        return JsonResponse({'error': 'Código NFC não encontrado'}, status=404)

def api_nfc_info_empresa(request, empresa_slug, codigo):
    """API para retornar informações do cartão NFC em JSON dentro de uma empresa"""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    try:
        cartao = NFCCard.objects.get(codigo_nfc=codigo, empresa=empresa, ativo=True)
        
        if cartao.pessoa:
            data = {
                'tipo': 'pessoa',
                'empresa': empresa.nome,
                'empresa_slug': empresa.slug,
                'nome': cartao.pessoa.nome,
                'email': cartao.pessoa.email,
                'telefone': cartao.pessoa.telefone,
                'cargo': cartao.pessoa.cargo,
                'apresentacao': cartao.pessoa.apresentacao,
                'url': request.build_absolute_uri(cartao.pessoa.get_absolute_url()),
                'foto': cartao.pessoa.foto.url if cartao.pessoa.foto else None,
            }
        elif cartao.pet:
            data = {
                'tipo': 'pet',
                'empresa': empresa.nome,
                'empresa_slug': empresa.slug,
                'nome': cartao.pet.nome,
                'especie': cartao.pet.get_especie_display(),
                'raca': cartao.pet.raca,
                'tutor': cartao.pet.tutor.nome,
                'tutor_telefone': cartao.pet.tutor.telefone,
                'url': request.build_absolute_uri(cartao.pet.get_absolute_url()),
                'foto': cartao.pet.foto.url if cartao.pet.foto else None,
            }
        else:
            return JsonResponse({'error': 'Cartão não associado'}, status=404)
            
        return JsonResponse(data)
        
    except NFCCard.DoesNotExist:
        return JsonResponse({'error': 'Código NFC não encontrado'}, status=404)
