from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config["DEBUG"] = True
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
	username="root",
	password="root",
	hostname="140.143.12.108",
	databasename="revelations")
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Schedule(db.Model):
	__tablename__ = "schedule"

	id = db.Column(db.Integer, primary_key=True)
	course_developer = db.Column(db.String(50))
	foreign_teacher = db.Column(db.String(50))
	slot_index = db.Column(db.Integer)
	event = db.Column(db.String(20))
	studio = db.Column(db.String(20))
	date = db.Column(db.String(10))

class Slot(db.Model):
    __tablename__ = "slot"

    id = db.Column(db.Integer, primary_key=True)
    foreign_teacher = db.Column(db.String(50))
    slot_index = db.Column(db.String(100))
    date = db.Column(db.String(10))
        

@app.route('/hello')
def hello():
    return 'Hello World'

@app.route('/arrange/<date>')
def arrange(date):
    ftGroup = db.session.query(Schedule).filter(Schedule.date==date).group_by(Schedule.foreign_teacher).all()
    allArrange = []
    for ftSchedule in ftGroup:
        arrangeList = {}
        ftArrange = db.session.query(Schedule).filter(Schedule.date==date, Schedule.foreign_teacher==ftSchedule.foreign_teacher).all()
        ftArrangeArray = []
        for schedule in ftArrange:
            scheduleJson = {}
            scheduleJson['ft'] = schedule.foreign_teacher
            scheduleJson['cd'] = schedule.course_developer
            scheduleJson['slotIndex'] = schedule.slot_index
            scheduleJson['event'] = schedule.event
            scheduleJson['studio'] = schedule.studio
            ftArrangeArray.append(scheduleJson)
        arrangeList['name'] = ftSchedule.foreign_teacher
        arrangeList['schedule'] = ftArrangeArray

        # 获取外教当天所有时间段的可预约状态
        slots = db.session.query(Slot).filter(Slot.date==date, Slot.foreign_teacher==ftSchedule.foreign_teacher).all()
        if slots:
            arrangeList['slot_status'] = slots.slot_index
        allArrange.append(arrangeList)
    db.session.close()
    return Response(json.dumps(allArrange), mimetype="text/json")

@app.route('/schedule/add', methods=['POST'])
def schedule():
    print(request.form.values())
    if request.method == 'POST':
        cd = request.form['cd']
        ft = request.form['ft']
        slotIndex = request.form['slot_index']
        event = request.form['event']
        studio = request.form['studio']
        date = request.form['date']
        
        if cd and ft and slotIndex and event and studio and date:
            newSchedule = Schedule(course_developer=cd, foreign_teacher=ft, slot_index=slotIndex, event=event, studio=studio, date=date)
            db.session.add(newSchedule)
            db.session.commit()
            db.session.close()
            return Response(json.dumps({'code': 1}), mimetype="text/json")
    result = json.dumps({'code': 2, 'msg': 'Paramter invalid'})
    return Response(result, mimetype="text/json")

@app.route('/slot/<date>/<ft>')
def slot(date, ft):
    slots = db.session.query(Slot).filter(Slot.date==date, Slot.foreign_teacher==ft).all()
    ftSlotsOfDay = {}
    ftSlotsOfDay['ft'] = ft
    ftSlotsOfDay['date'] = date
    ftSlotsOfDay['slot_indexs'] = slots.slot_index.split(",")
    Response(json.dumps(ftSlotsOfDay), mimetype="text/json")

@app.route('/slot/update', methods=['POST'])
def updateSlot():
    if request.method == 'POST':
        ft = request.form['ft']
        slotIndex = request.form['slot_index']
        date = request.form['date']
        if ft and slotIndex and date:
            newSlot = Slot(foreign_teacher=ft, slot_index=slotIndex, date=date)
            db.session.add(newSlot)
            db.session.commit()
            db.session.close()
            return Response(json.dumps({'code': 1}), mimetype="text/json")
    result = json.dumps({'code': 2, 'msg': 'Paramter invalid'})
    return Response(result, mimetype="text/json")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)