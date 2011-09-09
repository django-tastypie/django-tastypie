{% for key,endpoint in endpoints.items %}
{{endpoint.list_endpoint}}
----------------------------------------------------------


**Model Fields**:
{% for field, field_meta in endpoint.schema.fields.items %}
    ``{{field}}``:

        :Type:
            {{field_meta.type}}
        :Description: 
            {{field_meta.help_text}}
        :Nullable: 
            {{field_meta.nullable}}
        :Readonly:
            {{field_meta.readonly}} 
{% endfor %}

JSON Response ::

    {

    {% for field, field_meta in endpoint.schema.fields.items %} {{field}}:<{{field_meta.type}}>,
    {% endfor %}
    }


{% endfor %}
