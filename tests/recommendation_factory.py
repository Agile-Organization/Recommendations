"""
Test Factory to make fake objects for testing
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.model import Recommendation


class RecommendationFactory(factory.Factory):
    """ Creates fake Recommendations Objects """

    class Meta:
        """ Recommendation Factory uses Recommendation class as Meta model"""
        model = Recommendation

    product_id = FuzzyChoice(choices=range(1, 10001))
    related_product_id = FuzzyChoice(choices=range(10001, 20001))
    typeid = FuzzyChoice(choices=[1, 2, 3])
    status = FuzzyChoice(choices=[True, False])


if __name__ == "__main__":
    for _ in range(10):
        recommendation = RecommendationFactory()
        print(recommendation.serialize())
