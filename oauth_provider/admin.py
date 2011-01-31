from django.contrib import admin

from models import Resource, Consumer, Token

class ResourceAdmin(admin.ModelAdmin):
	pass
	
class ConsumerAdmin(admin.ModelAdmin):
	pass

class TokenAdmin(admin.ModelAdmin):
	pass
	

admin.site.register(Resource, ResourceAdmin)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(Token, TokenAdmin)