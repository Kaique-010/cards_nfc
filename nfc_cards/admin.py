from django.contrib import admin
from .models import Empresa, Person, Pet, NFCCard

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'email', 'telefone', 'criado_em', 'ativo']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'slug', 'email']
    readonly_fields = ['criado_em', 'atualizado_em']
    prepopulated_fields = {'slug': ('nome',)}
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao')
        }),
        ('Identidade Visual', {
            'fields': ('logo', 'cor_primaria', 'cor_secundaria')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'website', 'endereco')
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em', 'ativo'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'email', 'telefone', 'empresa', 'cargo', 'criado_em', 'ativo']
    list_filter = ['ativo', 'criado_em', 'empresa']
    search_fields = ['nome', 'slug', 'email', 'telefone', 'empresa__nome']
    readonly_fields = ['slug', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'email', 'telefone', 'whatsapp', 'foto')
        }),
        ('Informações Profissionais', {
            'fields': ('cargo', 'apresentacao')
        }),
        ('Redes Sociais', {
            'fields': ('linkedin', 'instagram', 'facebook', 'website', 'linktree_url'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('empresa')

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'especie', 'raca', 'tutor', 'empresa', 'criado_em', 'ativo']
    list_filter = ['ativo', 'especie', 'porte', 'criado_em', 'empresa']
    search_fields = ['nome', 'slug', 'raca', 'tutor__nome', 'empresa__nome']
    readonly_fields = ['slug', 'empresa', 'criado_em', 'atualizado_em', 'idade']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'especie', 'raca', 'porte', 'cor', 'data_nascimento', 'idade', 'foto')
        }),
        ('Tutor e Empresa', {
            'fields': ('tutor', 'empresa')
        }),
        ('Informações Médicas', {
            'fields': ('veterinario', 'telefone_veterinario', 'medicamentos', 'alergias'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tutor', 'empresa')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tutor":
            kwargs["queryset"] = Person.objects.filter(ativo=True).select_related('empresa')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(NFCCard)
class NFCCardAdmin(admin.ModelAdmin):
    list_display = ['codigo_nfc', 'tipo', 'get_owner', 'empresa', 'criado_em', 'ativo']
    list_filter = ['ativo', 'tipo', 'criado_em', 'empresa']
    search_fields = ['codigo_nfc', 'pessoa__nome', 'pet__nome', 'empresa__nome']
    readonly_fields = ['empresa', 'criado_em', 'atualizado_em', 'qr_code']
    
    def get_owner(self, obj):
        if obj.pessoa:
            return f"Pessoa: {obj.pessoa.nome}"
        elif obj.pet:
            return f"Pet: {obj.pet.nome}"
        return "Não definido"
    get_owner.short_description = "Proprietário"
    
    fieldsets = (
        ('Informações do Cartão', {
            'fields': ('codigo_nfc', 'tipo', 'pessoa', 'pet', 'empresa')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('empresa', 'pessoa', 'pet')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pessoa":
            kwargs["queryset"] = Person.objects.filter(ativo=True).select_related('empresa')
        elif db_field.name == "pet":
            kwargs["queryset"] = Pet.objects.filter(ativo=True).select_related('empresa', 'tutor')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)