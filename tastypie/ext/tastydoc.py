from django.http import HttpRequest
from sphinx.util.compat import make_admonition
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from docutils.core import Publisher, publish_doctree
from django.template import Context, Template
from docutils import nodes
from sphinx.util.compat import Directive
import os
import simplejson

def setup(app):
    app.add_directive('tastydoc', TastyDirective)


class TastyDirective(Directive):

    # this enables content in the directive
    has_content = True
    def run(self):
        module_parts = self.content[0].split(".")
        module = ".".join( module_parts[0:len(module_parts)-1] )
        member = module_parts[len(module_parts)-1]

        api_module = __import__( module, fromlist=['a'] )
        api = api_module.__dict__[member]

        parser = Parser()
        publisher = Publisher()
        request = HttpRequest()
        top_level_response = api.top_level( request, None ) 
        top_level_doc = simplejson.loads( top_level_response.content )

        for name in sorted(api._registry.keys()):        
            resource_dict = top_level_doc[name]
            resource = api._registry[name]
            schema = resource.build_schema()
            resource_dict['schema'] = schema
        path = os.path.dirname(__file__)
        rst_template = open(path + "/tasty-endpoint-template.rst").read()
        template_vars = {
                    'endpoints':top_level_doc,
                    }
        django_template = Template( rst_template )
        output_rst = django_template.render( Context(template_vars) ) 
        doctree = publish_doctree( output_rst )
        return doctree.children
