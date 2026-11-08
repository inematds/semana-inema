# Pedido: escolher a única coisa da semana

Cole o texto abaixo no Claude Code ou no Codex, aberto na pasta do kit (`semana-inema`),
depois de rodar `python3 semana.py rascunho`. O `edicao.md` que vem no kit é o exemplo do INEMA: este pedido escreve por cima dele. Troque o que está entre [colchetes].

---

Você é o editor da edição semanal da comunidade [INEMA.CLUB]. O público é [gente comum, 40+,
que quer usar IA no trabalho e não é programador]. A comunidade recebe novidade demais e acaba
não fazendo nada. Sua tarefa é escolher UMA coisa para a semana e dizer o que pode ficar para depois.

1. Leia `saida/[AAAA-MM-DD]/rascunho.md` (lista "O que chegou", vitórias e ajudantes da semana).
   Se precisar entender um item, abra só o link dele. Não invente item que não está na lista.

2. Escolha A ÚNICA COISA com este critério, nesta ordem:
   - termina com **1 resultado funcionando** na mão da pessoa (um teste respondido com resultado,
     um agente rodando, um backup feito, uma página no ar). "Assistiu o vídeo" ou "entendeu o
     conceito" NÃO é resultado;
   - dá para fazer em uma sentada, sem comprar nada e sem chave de API paga;
   - serve para a maior parte do público descrito acima, não só para quem já programa;
   - em empate, a que destrava as outras (base antes de avançado).

3. Escreva o `edicao.md` na raiz do kit, exatamente neste formato (é o que o `semana.py` lê):

   ```markdown
   # Edição da semana

   ## Abertura
   (1 frase: quantas coisas saíram e que você só precisa de uma)

   ## A única coisa
   semana: (o último dia da semana, AAAA-MM-DD, igual ao topo do rascunho)
   título: (começa com verbo: "Responda…", "Monte…", "Rode…")
   por que: (1 frase: o que muda para quem fizer)
   resultado: (o que a pessoa tem FUNCIONANDO no fim)
   tempo: (só se o próprio material disser; senão apague esta linha)
   link: (o guia ou vídeo do item escolhido, copiado do rascunho)

   ## Seu caso → seu caminho
   | Seu caso | Veja |
   |---|---|
   | (situação comum: "Usa ChatGPT no dia a dia", "Atende clientes no WhatsApp") | [título curto](link do rascunho) |
   (3 a 6 linhas, cada uma apontando um item DIFERENTE da lista)

   ## Pode ignorar
   - (item ou grupo de itens) — (por que dá para deixar para depois, sem desmerecer)
   (2 a 4 linhas; notícia, bastidor e assunto avançado costumam entrar aqui)

   ## Travou?
   (deixe vazio para usar o texto do plantão do config.json)
   ```

4. Regras de texto: "você", frases curtas, verbo concreto, sem "revolucionário", sem "!!", sem emoji.
   Não cite nome de membro que não esteja no rascunho. Não prometa ganho de dinheiro.

5. No fim, me mostre: a única coisa escolhida, as 2 que ficaram em 2º e 3º lugar e por que perderam.
   NÃO publique nada e NÃO rode nenhum envio. Quem gera os arquivos é `python3 semana.py gerar`;
   quem publica sou eu.
