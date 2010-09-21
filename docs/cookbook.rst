.. _ref-cookbook:

=================
Tastypie Cookbook
=================


Adding Custom Values
--------------------

You might encounter cases where you wish to include additional data in a
response which is not obtained from a field or method on your model. You can
easily extend the :meth:`~tastypie.resources.Resource.dehydrate` method to
provide additional values::

    class MyModelResource(Resource):
        class Meta:
            qs = MyModel.objects.all()

        def dehydrate(self, bundle):
            bundle.data['custom_field'] = "Whatever you want"
            return bundle



