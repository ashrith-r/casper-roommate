"""Exercise the actual Streamlit screens and a held-out real survey response."""
from pathlib import Path
import sys
import unittest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NITW_Roommate_Optimizer'))
from src.data.data_cleaner import load_data, PUBLIC_PATH, public_measurements, NUMERIC, HOBBIES

class AppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT/'NITW_Roommate_Optimizer'/'app.py'),default_timeout=60)

    def test_all_workspaces_and_setting_refresh(self):
        app=self.app().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,'98')
        for page in ['Pair explorer','Graph laboratory','Benchmarks','Survey evidence','Online matching','Delivery']:
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception,page)
        app.sidebar.radio[0].set_value('Overview').run()
        app.sidebar.slider[0].set_value(.75).run()
        self.assertTrue(any('previous run' in item.value for item in app.warning))
        self.assertTrue(all(item.proto.disabled for item in app.get('download_button')))
        next(button for button in app.button if button.label=='Run CASPER').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.result['settings']['lambda_'],.75)
        self.assertFalse(any('previous run' in item.value for item in app.warning))

    def test_online_append_uses_held_out_real_response(self):
        frame,_=load_data(PUBLIC_PATH)
        source=public_measurements(frame)
        existing,audit=load_data(source.iloc[:-1].to_csv(index=False).encode())
        new=source.iloc[-1]
        app=self.app()
        app.session_state.df=existing
        app.session_state.audit=audit
        app.session_state.result=None
        app.run()
        old_pairs={frozenset((existing.iloc[a].participant_id,existing.iloc[b].participant_id)) for a,b in app.session_state.result['pairs']}
        app.sidebar.radio[0].set_value('Online matching').run()
        app.text_input[0].set_value(new.participant_id)
        app.selectbox[0].set_value(new.gender)
        for widget in app.number_input:
            key=next(key for key in NUMERIC if key.replace('_',' ').title()==widget.label)
            widget.set_value(float(new[key]))
        app.multiselect[0].set_value([h for h in HOBBIES if new['hobby_'+h]])
        next(button for button in app.button if button.label=='Add response and update matches').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state.df),98)
        current=app.session_state.df
        actual={frozenset((current.iloc[a].participant_id,current.iloc[b].participant_id)) for a,b in app.session_state.result['pairs']}
        self.assertTrue(old_pairs<=actual)
        self.assertEqual(app.session_state.result['preserved_count'],len(old_pairs))
        self.assertEqual(current.iloc[-1].participant_id,new.participant_id)
        for key in NUMERIC:self.assertEqual(current.iloc[-1][key],new[key])

if __name__=='__main__':unittest.main()
