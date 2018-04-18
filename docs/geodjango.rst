.. _ref-geodjango:

=========
GeoDjango
=========

Tastypie features support for GeoDjango!  Resources return and accept 
`GeoJSON <http://geojson.org/geojson-spec.html>`_ (or similarly-formatted
analogs for other formats) and all `spatial lookup <https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoquerysets/#spatial-lookups>`_ filters are supported.  Distance lookups are not yet supported.

Usage
=====

Here's an example geographic model for leaving notes in polygonal
regions::


    from django.contrib.gis import models

    class GeoNote(models.Model):
        content = models.TextField()
        polys = models.MultiPolygonField(null=True, blank=True)
    
        objects = models.GeoManager()

To define a resource that takes advantage of the geospatial features,
we use ``tastypie.contrib.gis.resources.ModelResource``::

    from tastypie.contrib.gis.resources import ModelResource
    from tastypie.resources import ALL

    class GeoNoteResource(ModelResource):
        class Meta:
            resource_name = 'geonotes'
            queryset = GeoNote.objects.all()

            filtering = {
                'polys': ALL,
            }

Now when we do a ``GET`` on our GeoNoteResource we get back GeoJSON in
our response::

    {
        "content": "My note content",
        "id": "1",
        "polys": {
            "coordinates": [[[
                [-122.511067, 37.771276], [-122.510037, 37.766390999999999],
                [-122.510037, 37.763812999999999], [-122.456822, 37.765847999999998],
                [-122.45296, 37.766458999999998], [-122.454848, 37.773989999999998],
                [-122.475362, 37.773040000000002], [-122.511067, 37.771276]
            ]]],
            "type": "MultiPolygon"
        },
        "resource_uri": "/api/v1/geonotes/1/"
    }

When updating or creating new resources, simply provide GeoJSON or the
GeoJSON analog for your perferred format.

Filtering
---------

We can filter using any standard GeoDjango `spatial lookup <https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoquerysets/#spatial-lookups>`_ filter.  Simply provide a GeoJSON (or the analog) as a ``GET`` parameter value.

Let's find all of our ``GeoNote`` resources that contain a point inside
of `Golden Gate Park <https://sf.localwiki.org/Golden_Gate_Park>`_::

    /api/v1/geonotes/?polys__contains={"type": "Point", "coordinates": [-122.475233, 37.768617]}

Returns::

    {
        "meta": {
            "limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 1},
        "objects": [
            {
                "content": "My note content",
                "id": "1",
                "polys": {
                    "coordinates": [[[
                        [-122.511067, 37.771276], [-122.510037, 37.766390999999999],
                        [-122.510037, 37.763812999999999], [-122.456822, 37.765847999999998],
                        [-122.45296, 37.766458999999998], [-122.454848, 37.773989999999998],
                        [-122.475362, 37.773040000000002], [-122.511067, 37.771276]
                    ]]],
                    "type": "MultiPolygon"
                },
                "resource_uri": "/api/geonotes/1/"
            }
        ]
    }

We get back the ``GeoNote`` resource defining Golden Gate Park.
Awesome!
