from http import HTTPStatus
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector



class RecipeResource(Resource) :
    
    # 클라이언트로부터 /recipes/~3~ 이런식으로 바뀌는 숫자로 경로를 처리하므로 변수로 처리해준다.
    def get(self, recipe_id) :
        
        # DB에서, recipe_id 에 들어있는 값에 해당되는
        # 데이터를 select 해온다.
        
        try :
            connection = get_connection()

            query ='''select *
                    from recipe
                    where id = %s;'''
            record = (recipe_id, )

            #select 문은, dictionary = True를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            print(result_list)
            
            # 중요, DB에서 가져온 timestamp는
            # 파이썬의 datetime 으로 자동 변환된다.
            # 문제는, 이 데이터를 json으로 바로 보낼 수 없으므로
            # 문자열로 바꾼뒤 저장하여 보낸다.

            i = 0
            for record in result_list :
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
                i = i + 1

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503
        
        return {"result" : "success", "info" : result_list[0]}

    
    # 데이터를 업데이트하는 API들은 put 함수를 사용한다.
    @jwt_required()
    def put(self, recipe_id) :

        # body에서 전달된 데이터를 처리
        data = request.get_json()

        user_id = get_jwt_identity()

        # DB업데이트 실행코드
        try :
            # 데이터 업데이트
            # 1. DB에 연결
            connection = get_connection()

            ### 먼저 recipe_id 에 들어있는 user_id가
            ### 이 사람인지 먼저 확인한다.  

            query = '''select user_id
                    from recipe
                    where id = %s;'''

            record = (recipe_id, )

            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()

            recipe = result_list[0]

            if recipe['user_id'] != user_id :
                cursor.close()
                connection.close()
                return {'error' : '다른 이용자의 레시피를 수정할 수 없습니다.'}, 401 

            # 2. 쿼리문 만들기
            query = '''update recipe
                    set name = %s,
                    description = %s,
                    cook_time = %s,
                    directions = %s
                    where id = %s;'''

            record = (data['name'], data['description'], data['cook_time'], data['directions'], recipe_id)
            
            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => DB에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 503

        return {'result' : 'success'}, 200


    # 삭제하는 delete 함수
    def delete(self, recipe_id) :

        try :
            # 데이터 삭제
            # 1. DB에 연결
            connection = get_connection()

            # 2. 쿼리문 만들기
            query = '''delete from recipe
                    where id = %s;'''

            record = (recipe_id, )
            
            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => DB에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 503

        return {'result' : 'success'}, 200

# CRUD