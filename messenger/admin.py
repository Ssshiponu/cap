from django.contrib import admin
from django.utils.html import format_html
from .models import Message, Conversation

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'page_id', 'active', 'updated_at')
    search_fields = ('user_id', 'page_id')
    list_editable = ('active',)
    
    fields = ('user_id', 'page_id', 'render_conversation', 'updated_at', 'created_at')
    readonly_fields = ('user_id', 'page_id', 'render_conversation', 'updated_at', 'created_at')

    def render_conversation(self, obj):
        conv = obj.messages.all()  # limit for performance
        rows = "".join(
            f"<tr><td>{msg.role}</td><td>{str(msg.content)}</td></tr>"
            for msg in conv
        )
        table = (
            "<table style='max-width:600px'><thead><tr><th>Role</th><th>Message</th></tr></thead>"
            "<tbody>{}</tbody></table>"
        ).format(rows)
        return format_html(table)

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message)
