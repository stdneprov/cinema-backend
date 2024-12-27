import falcon.asgi
from falcon import HTTP_200, HTTP_400
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from catboost import CatBoostRegressor
import numpy as np
import falcon
from cors import CORSMiddleware
import joblib


class RecommendationAPI:
    def __init__(self, model):
        self.model = model

    async def on_post(self, req, resp):
        try:
            # Получение названия фильма из тела запроса
            raw_json = await req.stream.read()
            request_data = json.loads(raw_json.decode('utf-8'))
            liked_movie_title = request_data.get('title')

            if not liked_movie_title:
                raise ValueError("Title is required.")

            # Получение рекомендаций
            recommendations = recommend_movies(liked_movie_title, loaded_model, loaded_tfidf, loaded_movie_data)

            

            # Формирование ответа
            resp.status = HTTP_200
            resp.media = {
                "recommendations": recommendations.to_dict(orient='records')
            }
        except Exception as e:
            resp.status = HTTP_400
            resp.media = {
                "error": str(e)
            }



def load_model(model_path="model.pkl", tfidf_path="tfidf.pkl", data_path="movie_data.pkl"):
    """
    Загружает модель, TF-IDF векторизатор и данные о фильмах из файлов.
    model_path: Путь к файлу модели.
    tfidf_path: Путь к файлу TF-IDF векторизатора.
    data_path: Путь к файлу данных о фильмах.
    """
    model = joblib.load(model_path)
    tfidf = joblib.load(tfidf_path)
    movie_data = pd.read_pickle(data_path)
    return model, tfidf, movie_data

def recommend_movies(movie_title, model, tfidf, movie_data, top_n=10):
    """
    Рекомендует фильмы на основе названия.
    movie_title: Название фильма.
    model: Модель NearestNeighbors.
    tfidf: TF-IDF векторизатор.
    movie_data: DataFrame с данными о фильмах.
    top_n: Количество фильмов для рекомендации.
    """
    # Проверяем, существует ли фильм в базе
    if movie_title not in movie_data["title"].values:
        raise ValueError("Фильм с таким названием не найден в базе.")

    # Получаем индекс фильма
    movie_idx = movie_data[movie_data["title"] == movie_title].index[0]

    # Преобразуем описание фильма в вектор
    movie_vector = tfidf.transform([movie_data.iloc[movie_idx]["genres"]])

    # Ищем ближайших соседей
    distances, indices = model.kneighbors(movie_vector, n_neighbors=top_n + 1)

    # Исключаем сам фильм из рекомендаций
    similar_indices = indices.flatten()[1:]

    # Составляем DataFrame с рекомендациями
    recommendations = movie_data.iloc[similar_indices][["movieId", "title"]]
    recommendations["similarity_score"] = 1 - distances.flatten()[1:]

    # Фильтруем рекомендации, исключая фильм, который был выбран пользователем
    liked_movie_id = movie_data[movie_data["title"] == movie_title]["movieId"].values[0]
    recommendations = recommendations[recommendations["movieId"] != liked_movie_id]

    # Если количество рекомендаций меньше top_n, добавляем оставшиеся фильмы
    if len(recommendations) < top_n:
        # Ищем еще фильмы, которых нет в текущем списке рекомендаций
        additional_recommendations = movie_data[~movie_data["movieId"].isin(recommendations["movieId"])]

        # Сортируем по схожести и добавляем недостающие фильмы
        additional_recommendations = additional_recommendations.iloc[similar_indices[len(recommendations):len(recommendations) + (top_n - len(recommendations))]]
        additional_recommendations["similarity_score"] = 1 - distances.flatten()[len(recommendations):len(recommendations) + (top_n - len(recommendations))]

        # Объединяем данные
        recommendations = pd.concat([recommendations, additional_recommendations])
        # Убираем столбец 'genres' если он не нужен
        recommendations = recommendations.drop(columns=['genres'], errors='ignore')

    return recommendations.rename(columns={'movieId': 'id'})



def calculate_precision(data, liked_movie_title, recommendations, top_n=5):
    # Найдем фильм по названию, который пользователь оценил
    liked_movie_id = data.loc[data['title'] == liked_movie_title, 'movieId'].values[0]
    
    # Все фильмы, которые пользователи оценили, и оценки которых выше 4
    relevant_movies = data[(data['movieId'] != liked_movie_id) & (data['rating'] > 4)]
    
    # Из рекомендаций получаем список movieId
    recommended_movie_ids = recommendations['movieId'].values
    relevant_movie_ids = relevant_movies['movieId'].values
    
    # Находим пересечение рекомендованных и релевантных фильмов
    relevant_recommended = set(recommended_movie_ids) & set(relevant_movie_ids)
    
    # Precision@K: Число релевантных фильмов среди рекомендованных / K
    precision = len(relevant_recommended) / top_n if top_n > 0 else 0

    return precision

# Загрузка
loaded_model, loaded_tfidf, loaded_movie_data = load_model(
    model_path="model.pkl", 
    tfidf_path="tfidf.pkl", 
    data_path="movies_data.pkl"
)

# Рекомендации с использованием загруженной модели

# print(recommendations)


# Создание приложения Falcon для ASGI
cors_middleware = CORSMiddleware()
app = falcon.asgi.App(middleware=[cors_middleware])


recommendation_api = RecommendationAPI(loaded_model)
app.add_route('/recommend', recommendation_api)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
