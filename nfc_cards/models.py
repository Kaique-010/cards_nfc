from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class UserProfile(models.Model):
    """Perfil do usuário conectado a uma empresa"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True)
    is_empresa_owner = models.BooleanField(default=False, verbose_name="É proprietário da empresa")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"
    
    def __str__(self):
        empresa_nome = self.empresa.nome if self.empresa else "Sem empresa"
        return f"{self.user.get_full_name() or self.user.username} - {empresa_nome}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil quando um usuário é criado"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Empresa(models.Model):
    # Informações básicas
    nome = models.CharField(max_length=100, verbose_name="Nome da Empresa")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    
    # Identidade visual
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True, verbose_name="Logo")
    cor_primaria = models.CharField(max_length=7, default="#007bff", verbose_name="Cor Primária", help_text="Formato: #RRGGBB")
    cor_secundaria = models.CharField(max_length=7, default="#6c757d", verbose_name="Cor Secundária", help_text="Formato: #RRGGBB")
    
    # Contato
    email = models.EmailField(blank=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    website = models.URLField(blank=True, verbose_name="Website")
    
    # Endereço
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('empresa_home', kwargs={'empresa_slug': self.slug})

class Person(models.Model):
    # Relacionamento com empresa
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pessoas', verbose_name="Empresa")
    
    # Identificação única por empresa
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    
    # Informações básicas
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp")
    
    # Informações profissionais
    cargo = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    
    # Apresentação
    apresentacao = models.TextField(verbose_name="Apresentação", help_text="Breve apresentação pessoal")
    
    # Foto de perfil
    foto = models.ImageField(upload_to='pessoas/', blank=True, null=True, verbose_name="Foto de Perfil")
    
    # Redes sociais
    linkedin = models.URLField(blank=True, verbose_name="LinkedIn")
    instagram = models.URLField(blank=True, verbose_name="Instagram")
    facebook = models.URLField(blank=True, verbose_name="Facebook")
    website = models.URLField(blank=True, verbose_name="Website")
    
    # Linktree
    linktree_url = models.URLField(blank=True, verbose_name="Linktree")
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        ordering = ['nome']
        unique_together = ['empresa', 'slug']
    
    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            counter = 1
            while Person.objects.filter(empresa=self.empresa, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('person_detail', kwargs={'empresa_slug': self.empresa.slug, 'person_slug': self.slug})

class Pet(models.Model):
    ESPECIES = [
        ('cao', 'Cão'),
        ('gato', 'Gato'),
        ('passaro', 'Pássaro'),
        ('peixe', 'Peixe'),
        ('outro', 'Outro'),
    ]
    
    PORTES = [
        ('pequeno', 'Pequeno'),
        ('medio', 'Médio'),
        ('grande', 'Grande'),
    ]
    
    # Relacionamento com empresa (através do tutor)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pets', verbose_name="Empresa")
    
    # Identificação única por empresa
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    
    # Informações básicas
    nome = models.CharField(max_length=50, verbose_name="Nome do Pet")
    especie = models.CharField(max_length=20, choices=ESPECIES, verbose_name="Espécie")
    raca = models.CharField(max_length=50, blank=True, verbose_name="Raça")
    porte = models.CharField(max_length=20, choices=PORTES, blank=True, verbose_name="Porte")
    cor = models.CharField(max_length=50, blank=True, verbose_name="Cor")
    
    # Datas importantes
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    
    # Foto
    foto = models.ImageField(upload_to='pets/', blank=True, null=True, verbose_name="Foto do Pet")
    
    # Informações médicas
    veterinario = models.CharField(max_length=100, blank=True, verbose_name="Veterinário")
    telefone_veterinario = models.CharField(max_length=20, blank=True, verbose_name="Telefone do Veterinário")
    
    # Informações especiais
    observacoes = models.TextField(blank=True, verbose_name="Observações Especiais")
    medicamentos = models.TextField(blank=True, verbose_name="Medicamentos")
    alergias = models.TextField(blank=True, verbose_name="Alergias")
    
    # Relacionamento com tutor
    tutor = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='pets', verbose_name="Tutor")
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        ordering = ['nome']
        unique_together = ['empresa', 'slug']
    
    def __str__(self):
        return f"{self.nome} ({self.tutor.nome} - {self.empresa.nome})"
    
    def save(self, *args, **kwargs):
        # Definir empresa baseada no tutor
        if self.tutor:
            self.empresa = self.tutor.empresa
        
        # Gerar slug único
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            counter = 1
            while Pet.objects.filter(empresa=self.empresa, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('pet_detail', kwargs={'empresa_slug': self.empresa.slug, 'pet_slug': self.slug})
    
    @property
    def idade(self):
        if self.data_nascimento:
            from datetime import date
            today = date.today()
            return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
        return None

class NFCCard(models.Model):
    TIPOS = [
        ('pessoa', 'Cartão de Visita'),
        ('pet', 'Carteirinha de Pet'),
    ]
    
    # Relacionamento com empresa
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cartoes_nfc', verbose_name="Empresa")
    
    # Identificação única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_nfc = models.CharField(max_length=50, unique=True, verbose_name="Código NFC")
    tipo = models.CharField(max_length=20, choices=TIPOS, verbose_name="Tipo de Cartão")
    
    # Relacionamentos (apenas um será preenchido)
    pessoa = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name='cartoes_nfc')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, blank=True, null=True, related_name='cartoes_nfc')
    
    # QR Code para backup
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="QR Code")
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Cartão NFC"
        verbose_name_plural = "Cartões NFC"
        ordering = ['-criado_em']
    
    def __str__(self):
        if self.pessoa:
            return f"Cartão NFC - {self.pessoa.nome} ({self.empresa.nome})"
        elif self.pet:
            return f"Cartão NFC - {self.pet.nome} ({self.empresa.nome})"
        return f"Cartão NFC - {self.codigo_nfc} ({self.empresa.nome})"
    
    def save(self, *args, **kwargs):
        # Definir empresa baseada na pessoa ou pet
        if self.pessoa:
            self.empresa = self.pessoa.empresa
        elif self.pet:
            self.empresa = self.pet.empresa
        
        # Gerar QR Code automaticamente
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        if self.pessoa:
            url = f"https://seudominio.com/{self.empresa.slug}/pessoa/{self.pessoa.slug}/"
        elif self.pet:
            url = f"https://seudominio.com/{self.empresa.slug}/pet/{self.pet.slug}/"
        else:
            return
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f'qr_{self.codigo_nfc}.png'
        self.qr_code.save(filename, File(buffer), save=False)
    
    def get_target_url(self):
        if self.pessoa:
            return reverse('person_detail', kwargs={'empresa_slug': self.empresa.slug, 'person_slug': self.pessoa.slug})
        elif self.pet:
            return reverse('pet_detail', kwargs={'empresa_slug': self.empresa.slug, 'pet_slug': self.pet.slug})
        return None