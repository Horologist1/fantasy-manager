export const monthly_card_recipe = {
  id:'monthly_card', title:'Monthly condition', kind:'monthly_card',
  description:'Add a card to the full monthly catalog, then configure its effects in the editor.',
  default_output:'monthly_conditions/cards.json',
  steps:[
    {id:'id',type:'string',label:'Unique card id',required:true},
    {id:'name',type:'string',label:'Card title',required:true},
    {id:'description',type:'longtext',label:'Description (up to 500 characters)',required:true},
    {id:'weight',type:'float',label:'Draw weight (0 disables random selection)',default:1,min:0,max:10000},
    {id:'nsfw',type:'bool',label:'NSFW card',default:false},
  ],
  build:a => ({id:a.id,name:a.name,description:a.description,weight:a.weight ?? 1,nsfw:!!a.nsfw,image:'',effects:[]}),
};
