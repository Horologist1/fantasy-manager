// Keep these bounds aligned with fm_monthly.conditions.validate_card.
const selectors = {
  buildings: {type: 'list_of_strings', catalog: 'all_buildings'},
  professions: {type: 'list_of_strings', catalog: 'all_professions'},
  skills: {type: 'list_of_strings', catalog: 'all_skills'},
};
const rule = (id, field, message, check) => ({id, field, message, check, severity:'error'});
const number = (v, lo, hi) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
export const monthly_card_schema = {
  id: 'monthly_card',
  fields: {
    id: {type:'string', required:true, unique_in_file:true},
    name: {type:'string', required:true},
    description: {type:'longtext', required:true},
    weight: {type:'float', min:0, max:10000},
    image: {type:'string'},
    nsfw: {type:'bool'},
    effects: {type:'list_of_objects', item_fields:{
      type: {type:'enum', options:['skill','earnings'], required:true},
      value: {type:'float', required:true}, ...selectors,
    }},
  },
  rules: [
    ...['id','name','description'].map(k => rule('monthly_'+k, k,
      `Use non-empty text, at most ${k === 'description' ? 500 : 80} characters.`,
      e => typeof e[k] === 'string' && !!e[k].trim() && Array.from(e[k]).length <= (k === 'description' ? 500 : 80))),
    rule('monthly_weight','weight','Weight must be between 0 and 10000.', e => number(e.weight === undefined ? 1 : e.weight,0,10000)),
    rule('monthly_image','image','Use an existing images/ PNG, JPG, JPEG or WebP path, or leave it empty.', e => e.image === undefined || (typeof e.image === 'string' && (!e.image || (e.image.startsWith('images/') && !/\.\.|\\|:/.test(e.image) && /\.(png|jpe?g|webp)$/i.test(e.image))))),
    rule('monthly_rating','nsfw','NSFW must be true or false.', e => e.nsfw === undefined || typeof e.nsfw === 'boolean'),
    rule('monthly_effects','effects','Use at most three effects. Skill: -10 to +10 with skills selected. Earnings: 0.90 to 1.15 without skills. Select buildings or professions.', e => {
      const effects = e.effects === undefined ? [] : e.effects;
      return Array.isArray(effects) && effects.length <= 3 && (e.id !== 'quiet_month' || !effects.length) && effects.every(f => {
        if (!f || !['skill','earnings'].includes(f.type)) return false;
        if (!number(f.value, f.type === 'skill' ? -10 : .9, f.type === 'skill' ? 10 : 1.15)) return false;
        if (!Object.keys(selectors).every(k => f[k] === undefined || (Array.isArray(f[k]) && f[k].every(v => typeof v === 'string' && v.length > 0)))) return false;
        return ((f.buildings || []).length || (f.professions || []).length) && (f.type === 'skill' ? (f.skills || []).length > 0 : !(f.skills || []).length);
      });
    }),
    ...Object.keys(selectors).map(k => rule('monthly_selector_'+k, 'effects', 'Unknown '+k+' identifier.', (e,ctx) => {
      const known = ctx?.catalogs?.[selectors[k].catalog];
      return !known || (e.effects || []).every(f => (f[k] || []).every(v => known.has(v)));
    })),
  ],
};

export const monthly_card_editor_sections = [{
  id:'monthly', label:'Monthly condition',
  fields:Object.entries(monthly_card_schema.fields).map(([id,def]) => ({id,label:({id:'Card ID',name:'Title',description:'Description',weight:'Draw weight',image:'Optional image',nsfw:'NSFW',effects:'Effects'})[id],...def,
    ...(id === 'effects' ? {hint:'Up to three effects. Building and profession filters must both match when filled. Empty filters match all. Earnings 1.10 means +10%.'} : {}),
    ...(id === 'image' ? {hint:'Optional existing game image. Overrides do not import new artwork.'} : {}),
  })),
}];
